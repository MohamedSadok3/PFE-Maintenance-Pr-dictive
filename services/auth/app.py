import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from psycopg2.extras import RealDictCursor

load_dotenv()

POSTGRES_URL = os.environ.get("POSTGRES_URL")
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_EXPIRES_HOURS = 8
COMPONENT_TYPES = {"moteur", "pompe", "compresseur", "echangeur"}

app = Flask(__name__)
CORS(app)


def get_db_connection():
    if not POSTGRES_URL:
        raise RuntimeError("POSTGRES_URL is not configured.")
    return psycopg2.connect(POSTGRES_URL)


def _serialize_user(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "role": row["role"],
        "machines": row["machines"] or [],
        "last_login": row["last_login"].isoformat() if row["last_login"] else None,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


def _serialize_component(row):
    return {
        "id": row["id"],
        "key": row["key"],
        "name": row["name"],
        "type": row["type"],
        "enabled": bool(row["enabled"]),
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


def create_token(user):
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured.")
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "machines": user["machines"] or [],
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRES_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def require_auth(roles=None):
    roles = roles or []

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "Unauthorized"}), 401

            token = auth_header.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            except jwt.InvalidTokenError:
                return jsonify({"error": "Unauthorized"}), 401

            if roles and payload.get("role") not in roles:
                return jsonify({"error": "Forbidden"}), 403

            g.current_user = payload
            return func(*args, **kwargs)

        return wrapped

    return decorator


def init_db():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'superviseur', 'technicien')),
                    machines TEXT[] DEFAULT ARRAY[]::TEXT[],
                    last_login TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS components (
                    id SERIAL PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    enabled BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
            cur.execute("ALTER TABLE components ADD COLUMN IF NOT EXISTS type TEXT;")

            cur.execute("SELECT id FROM users WHERE email = %s;", ("admin@smartmaintain.com",))
            existing_admin = cur.fetchone()

            if not existing_admin:
                hashed = bcrypt.hashpw("Admin1234".encode("utf-8"), bcrypt.gensalt()).decode(
                    "utf-8"
                )
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role, machines)
                    VALUES (%s, %s, %s, %s, %s);
                    """,
                    ("Admin", "admin@smartmaintain.com", hashed, "admin", []),
                )

            default_components = [
                ("moteur", "Moteur", "moteur"),
                ("pompe", "Pompe", "pompe"),
                ("compresseur", "Compresseur", "compresseur"),
                ("echangeur", "Échangeur Thermique", "echangeur"),
            ]
            for component_key, component_name, component_type in default_components:
                cur.execute(
                    """
                    INSERT INTO components (key, name, type, enabled)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET type = EXCLUDED.type, name = EXCLUDED.name;
                    """,
                    (component_key, component_name, component_type, True),
                )
            cur.execute(
                """
                UPDATE components
                SET type = CASE
                    WHEN key IN ('moteur', 'pompe', 'compresseur', 'echangeur') THEN key
                    ELSE COALESCE(NULLIF(type, ''), 'moteur')
                END
                WHERE type IS NULL OR type = '';
                """
            )
            cur.execute("ALTER TABLE components DROP CONSTRAINT IF EXISTS components_type_check;")
            cur.execute(
                """
                ALTER TABLE components
                ADD CONSTRAINT components_type_check
                CHECK (type IN ('moteur', 'pompe', 'compresseur', 'echangeur'));
                """
            )

            # Keep DB role constraint aligned with current application roles.
            cur.execute(
                """
                UPDATE users
                SET role = 'technicien'
                WHERE role = 'viewer';
                """
            )
            cur.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;")
            cur.execute(
                """
                ALTER TABLE users
                ADD CONSTRAINT users_role_check
                CHECK (role IN ('admin', 'superviseur', 'technicien'));
                """
            )
            conn.commit()


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, email, password_hash, role, machines, last_login, created_at
                FROM users
                WHERE email = %s;
                """,
                (email,),
            )
            user = cur.fetchone()

            if not user or not bcrypt.checkpw(
                password.encode("utf-8"), user["password_hash"].encode("utf-8")
            ):
                return jsonify({"error": "Invalid credentials."}), 401

            cur.execute("UPDATE users SET last_login = NOW() WHERE id = %s;", (user["id"],))
            conn.commit()

    token = create_token(user)
    return jsonify(
        {
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "role": user["role"],
                "machines": user["machines"] or [],
            },
        }
    )


@app.route("/api/auth/me", methods=["GET"])
@require_auth()
def me():
    user_id = g.current_user.get("sub")
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, email, role, machines, last_login, created_at
                FROM users
                WHERE id = %s;
                """,
                (user_id,),
            )
            user = cur.fetchone()

    if not user:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"user": _serialize_user(user)})


@app.route("/api/users", methods=["GET"])
@require_auth(["admin", "superviseur"])
def list_users():
    role = request.args.get("role")
    current_role = g.current_user.get("role")

    # Supervisors can only load technicians for assignment workflows.
    if current_role == "superviseur" and role != "technicien":
        return jsonify({"error": "Forbidden"}), 403

    filters = []
    values = []
    if role:
        filters.append("role = %s")
        values.append(role)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT id, name, email, role, machines, last_login, created_at
                FROM users
                {where_clause}
                ORDER BY id ASC;
                """,
                tuple(values),
            )
            users = cur.fetchall()

    return jsonify({"users": [_serialize_user(user) for user in users]})


@app.route("/api/users", methods=["POST"])
@require_auth(["admin"])
def create_user():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    role = data.get("role")
    machines = data.get("machines", [])

    if not all([name, email, password, role]):
        return jsonify({"error": "name, email, password and role are required."}), 400
    if role not in {"admin", "superviseur", "technicien"}:
        return jsonify({"error": "Invalid role."}), 400
    if not isinstance(machines, list):
        return jsonify({"error": "machines must be an array."}), 400

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role, machines)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, name, email, role, machines, last_login, created_at;
                    """,
                    (name, email, password_hash, role, machines),
                )
                user = cur.fetchone()
                conn.commit()
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({"error": "Email already exists."}), 409

    return jsonify({"user": _serialize_user(user)}), 201


@app.route("/api/users/<int:user_id>", methods=["PATCH"])
@require_auth(["admin"])
def update_user(user_id):
    data = request.get_json(silent=True) or {}

    fields = []
    values = []

    if "name" in data:
        fields.append("name = %s")
        values.append(data["name"])
    if "email" in data:
        normalized_email = (data["email"] or "").strip().lower()
        fields.append("email = %s")
        values.append(normalized_email)
    if "role" in data:
        if data["role"] not in {"admin", "superviseur", "technicien"}:
            return jsonify({"error": "Invalid role."}), 400
        fields.append("role = %s")
        values.append(data["role"])
    if "machines" in data:
        if not isinstance(data["machines"], list):
            return jsonify({"error": "machines must be an array."}), 400
        fields.append("machines = %s")
        values.append(data["machines"])
    if "password" in data:
        hashed = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        fields.append("password_hash = %s")
        values.append(hashed)

    if not fields:
        return jsonify({"error": "No valid fields to update."}), 400

    values.append(user_id)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                UPDATE users
                SET {", ".join(fields)}
                WHERE id = %s
                RETURNING id, name, email, role, machines, last_login, created_at;
                """,
                tuple(values),
            )
            user = cur.fetchone()
            conn.commit()

    if not user:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"user": _serialize_user(user)})


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@require_auth(["admin"])
def delete_user(user_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
            deleted = cur.rowcount
            conn.commit()

    if not deleted:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"message": "User deleted successfully."})


@app.route("/api/components", methods=["GET"])
@require_auth(["admin", "superviseur", "technicien"])
def list_components():
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, key, name, type, enabled, created_at, updated_at
                FROM components
                ORDER BY id ASC;
                """
            )
            rows = cur.fetchall()
    return jsonify({"components": [_serialize_component(row) for row in rows]})


@app.route("/api/components", methods=["POST"])
@require_auth(["admin"])
def create_component():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    component_type = (data.get("type") or "").strip().lower()
    enabled = bool(data.get("enabled", True))

    if not name or not component_type:
        return jsonify({"error": "name and type are required."}), 400
    if component_type not in COMPONENT_TYPES:
        return jsonify({"error": "Invalid component type."}), 400

    safe_name = "".join(ch for ch in name.lower() if ch.isalnum())
    if not safe_name:
        safe_name = "component"
    key = f"{safe_name}-{int(datetime.now(timezone.utc).timestamp())}"

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO components (key, name, type, enabled)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, key, name, type, enabled, created_at, updated_at;
                    """,
                    (key, name, component_type, enabled),
                )
                row = cur.fetchone()
                conn.commit()
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({"error": "Component key already exists."}), 409

    return jsonify({"component": _serialize_component(row)}), 201


@app.route("/api/components/<int:component_id>", methods=["PATCH"])
@require_auth(["admin"])
def update_component(component_id):
    data = request.get_json(silent=True) or {}
    fields = []
    values = []

    if "name" in data:
        name = (data.get("name") or "").strip()
        if not name:
            return jsonify({"error": "name cannot be empty."}), 400
        fields.append("name = %s")
        values.append(name)
    if "type" in data:
        component_type = (data.get("type") or "").strip().lower()
        if component_type not in COMPONENT_TYPES:
            return jsonify({"error": "Invalid component type."}), 400
        fields.append("type = %s")
        values.append(component_type)
    if "enabled" in data:
        fields.append("enabled = %s")
        values.append(bool(data.get("enabled")))

    if not fields:
        return jsonify({"error": "No valid fields to update."}), 400

    fields.append("updated_at = NOW()")
    values.append(component_id)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(
                    f"""
                    UPDATE components
                    SET {", ".join(fields)}
                    WHERE id = %s
                    RETURNING id, key, name, type, enabled, created_at, updated_at;
                    """,
                    tuple(values),
                )
                row = cur.fetchone()
                conn.commit()
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({"error": "Component key already exists."}), 409

    if not row:
        return jsonify({"error": "Component not found."}), 404

    return jsonify({"component": _serialize_component(row)})


@app.route("/api/components/<int:component_id>", methods=["DELETE"])
@require_auth(["admin"])
def delete_component(component_id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM components WHERE id = %s;", (component_id,))
            deleted = cur.rowcount
            conn.commit()

    if not deleted:
        return jsonify({"error": "Component not found."}), 404
    return jsonify({"message": "Component deleted successfully."})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "auth"})


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False)
