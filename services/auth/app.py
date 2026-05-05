import os
from datetime import datetime, timedelta, timezone
from functools import wraps
import re

import bcrypt
import jwt
import psycopg2
import requests
from psycopg2 import errors
from dotenv import load_dotenv
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from psycopg2.extras import Json, RealDictCursor

load_dotenv()

POSTGRES_URL = os.environ.get("POSTGRES_URL")
JWT_SECRET = os.environ.get("JWT_SECRET")
JWT_EXPIRES_HOURS = 8
COMPONENT_TYPES = {"moteur", "pompe", "compresseur", "echangeur"}
PLANT_CODE_PATTERN = re.compile(r"^[a-z0-9-]{3,32}$")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.environ.get("RESEND_FROM_EMAIL")
RESEND_API_URL = os.environ.get("RESEND_API_URL", "https://api.resend.com/emails")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:3000")

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
        "plant_id": row.get("plant_id"),
        "last_login": row["last_login"].isoformat() if row["last_login"] else None,
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
    }


def _serialize_component(row):
    return {
        "id": row["id"],
        "key": row["key"],
        "name": row["name"],
        "type": row["type"],
        "plant_id": row.get("plant_id"),
        "enabled": bool(row["enabled"]),
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


def _serialize_plant(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "code": row["code"],
        "status": row["status"],
        "contact_name": row.get("contact_name"),
        "contact_email": row.get("contact_email"),
        "contact_phone": row.get("contact_phone"),
        "location": row.get("location"),
        "industry": row.get("industry"),
        "description": row.get("description"),
        "approved_by": row.get("approved_by"),
        "approved_at": row["approved_at"].isoformat() if row.get("approved_at") else None,
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


def send_registration_approved_email(
    recipient_email,
    recipient_name,
    plant_name,
    plant_code,
):
    if not RESEND_API_KEY or not RESEND_FROM_EMAIL:
        app.logger.warning("Skipping approval email: Resend is not configured.")
        return False
    if not recipient_email:
        return False

    login_url = f"{APP_BASE_URL.rstrip('/')}/login"
    subject = f"Inscription de l'usine {plant_name} approuvee"
    body = (
        f"Bonjour {recipient_name or ''},\n\n"
        f"L'inscription de votre usine a ete approuvee.\n\n"
        f"Nom de l'usine: {plant_name}\n"
        f"Code usine: {plant_code}\n\n"
        f"Vous pouvez vous connecter ici: {login_url}\n\n"
        "Cordialement,\n"
        "Equipe SmartMaintain"
    )

    response = requests.post(
        RESEND_API_URL,
        headers={
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "from": RESEND_FROM_EMAIL,
            "to": [recipient_email],
            "subject": subject,
            "text": body,
        },
        timeout=10,
    )
    response.raise_for_status()
    return True


def create_token(user):
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured.")
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "machines": user["machines"] or [],
        "plant_id": user.get("plant_id"),
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
                CREATE TABLE IF NOT EXISTS plants (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    code TEXT UNIQUE NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
                    contact_name TEXT NULL,
                    contact_email TEXT NULL,
                    contact_phone TEXT NULL,
                    location TEXT NULL,
                    industry TEXT NULL,
                    description TEXT NULL,
                    approved_by INT NULL,
                    approved_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
            cur.execute("ALTER TABLE plants ADD COLUMN IF NOT EXISTS contact_name TEXT NULL;")
            cur.execute("ALTER TABLE plants ADD COLUMN IF NOT EXISTS contact_email TEXT NULL;")
            cur.execute("ALTER TABLE plants ADD COLUMN IF NOT EXISTS contact_phone TEXT NULL;")
            cur.execute("ALTER TABLE plants ADD COLUMN IF NOT EXISTS location TEXT NULL;")
            cur.execute("ALTER TABLE plants ADD COLUMN IF NOT EXISTS industry TEXT NULL;")
            cur.execute("ALTER TABLE plants ADD COLUMN IF NOT EXISTS description TEXT NULL;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS plant_registrations (
                    id SERIAL PRIMARY KEY,
                    plant_name TEXT NOT NULL,
                    plant_code TEXT NOT NULL,
                    contact_name TEXT NOT NULL,
                    contact_email TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                    review_note TEXT NULL,
                    reviewed_by INT NULL,
                    reviewed_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('superadmin', 'admin', 'superviseur', 'technicien')),
                    plant_id INT NULL REFERENCES plants(id) ON DELETE SET NULL,
                    machines TEXT[] DEFAULT ARRAY[]::TEXT[],
                    last_login TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plant_id INT NULL;")
            cur.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.table_constraints
                        WHERE table_name = 'users' AND constraint_name = 'users_plant_id_fkey'
                    ) THEN
                        ALTER TABLE users
                        ADD CONSTRAINT users_plant_id_fkey
                        FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE SET NULL;
                    END IF;
                END $$;
                """
            )
            cur.execute(
                """
                ALTER TABLE users DROP CONSTRAINT IF EXISTS users_plant_id_fkey;
                ALTER TABLE users
                ADD CONSTRAINT users_plant_id_fkey
                FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE;
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS components (
                    id SERIAL PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    plant_id INT NULL REFERENCES plants(id) ON DELETE CASCADE,
                    enabled BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                """
            )
            cur.execute("ALTER TABLE components ADD COLUMN IF NOT EXISTS type TEXT;")
            cur.execute("ALTER TABLE components ADD COLUMN IF NOT EXISTS plant_id INT NULL;")
            cur.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;")
            cur.execute(
                """
                ALTER TABLE users
                ADD CONSTRAINT users_role_check
                CHECK (role IN ('superadmin', 'admin', 'superviseur', 'technicien'));
                """
            )

            cur.execute("SELECT id FROM users WHERE email = %s;", ("superadmin@smartmaintain.com",))
            existing_superadmin = cur.fetchone()
            if not existing_superadmin:
                hashed = bcrypt.hashpw("SuperAdmin1234".encode("utf-8"), bcrypt.gensalt()).decode(
                    "utf-8"
                )
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role, machines, plant_id)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    ("Super Admin", "superadmin@smartmaintain.com", hashed, "superadmin", [], None),
                )

            cur.execute("SELECT id FROM users WHERE email = %s;", ("admin@smartmaintain.com",))
            existing_admin = cur.fetchone()
            cur.execute(
                """
                INSERT INTO plants (name, code, status)
                VALUES (%s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    name = EXCLUDED.name,
                    contact_name = COALESCE(plants.contact_name, %s),
                    contact_email = COALESCE(plants.contact_email, %s)
                RETURNING id;
                """,
                ("Usine Demo", "usine-demo", "active", "Contact Demo", "contact@usine-demo.local"),
            )
            demo_plant_id = cur.fetchone()["id"]

            if not existing_admin:
                hashed = bcrypt.hashpw("Admin1234".encode("utf-8"), bcrypt.gensalt()).decode(
                    "utf-8"
                )
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role, machines, plant_id)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    ("Admin", "admin@smartmaintain.com", hashed, "admin", [], demo_plant_id),
                )
            cur.execute(
                """
                UPDATE users
                SET plant_id = %s
                WHERE role != 'superadmin' AND plant_id IS NULL;
                """,
                (demo_plant_id,),
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
                    INSERT INTO components (key, name, type, plant_id, enabled)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (key) DO UPDATE
                    SET type = EXCLUDED.type, name = EXCLUDED.name, plant_id = EXCLUDED.plant_id;
                    """,
                    (component_key, component_name, component_type, demo_plant_id, True),
                )
            cur.execute(
                """
                UPDATE components
                SET plant_id = %s
                WHERE plant_id IS NULL;
                """,
                (demo_plant_id,),
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
                CHECK (role IN ('superadmin', 'admin', 'superviseur', 'technicien'));
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
                SELECT id, name, email, password_hash, role, plant_id, machines, last_login, created_at
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
                "plant_id": user.get("plant_id"),
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
                SELECT id, name, email, role, plant_id, machines, last_login, created_at
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
@require_auth(["superadmin", "admin", "superviseur"])
def list_users():
    role = request.args.get("role")
    plant_id = request.args.get("plant_id")
    current_role = g.current_user.get("role")
    current_plant_id = g.current_user.get("plant_id")

    # Supervisors can only load technicians for assignment workflows.
    if current_role == "superviseur" and role != "technicien":
        return jsonify({"error": "Forbidden"}), 403

    filters = []
    values = []
    if role:
        filters.append("role = %s")
        values.append(role)
    if current_role in {"admin", "superviseur"}:
        filters.append("plant_id = %s")
        values.append(current_plant_id)
        filters.append("role != %s")
        values.append("superadmin")
    elif plant_id:
        filters.append("plant_id = %s")
        values.append(int(plant_id))

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT id, name, email, role, plant_id, machines, last_login, created_at
                FROM users
                {where_clause}
                ORDER BY id ASC;
                """,
                tuple(values),
            )
            users = cur.fetchall()

    return jsonify({"users": [_serialize_user(user) for user in users]})


@app.route("/api/users", methods=["POST"])
@require_auth(["superadmin", "admin"])
def create_user():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")
    role = data.get("role")
    machines = data.get("machines", [])
    plant_id = data.get("plant_id")
    current_role = g.current_user.get("role")
    current_plant_id = g.current_user.get("plant_id")

    if not all([name, email, password, role]):
        return jsonify({"error": "name, email, password and role are required."}), 400
    if role not in {"superadmin", "admin", "superviseur", "technicien"}:
        return jsonify({"error": "Invalid role."}), 400
    if current_role != "superadmin" and role == "superadmin":
        return jsonify({"error": "Forbidden"}), 403
    if not isinstance(machines, list):
        return jsonify({"error": "machines must be an array."}), 400
    if current_role == "superadmin":
        if role != "superadmin" and not plant_id:
            return jsonify({"error": "plant_id is required for non-superadmin users."}), 400
    else:
        plant_id = current_plant_id

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role, plant_id, machines)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, name, email, role, plant_id, machines, last_login, created_at;
                    """,
                    (name, email, password_hash, role, plant_id, machines),
                )
                user = cur.fetchone()
                conn.commit()
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({"error": "Email already exists."}), 409

    return jsonify({"user": _serialize_user(user)}), 201


@app.route("/api/users/<int:user_id>", methods=["PATCH"])
@require_auth(["superadmin", "admin"])
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    current_role = g.current_user.get("role")
    current_plant_id = g.current_user.get("plant_id")

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
        if data["role"] not in {"superadmin", "admin", "superviseur", "technicien"}:
            return jsonify({"error": "Invalid role."}), 400
        if current_role != "superadmin" and data["role"] == "superadmin":
            return jsonify({"error": "Forbidden"}), 403
        fields.append("role = %s")
        values.append(data["role"])
    if "plant_id" in data:
        if current_role != "superadmin":
            return jsonify({"error": "Only superadmin can change plant_id."}), 403
        fields.append("plant_id = %s")
        values.append(data["plant_id"])
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
            if current_role != "superadmin":
                cur.execute(
                    "SELECT id FROM users WHERE id = %s AND plant_id = %s;",
                    (user_id, current_plant_id),
                )
                if not cur.fetchone():
                    return jsonify({"error": "Forbidden"}), 403
            cur.execute(
                f"""
                UPDATE users
                SET {", ".join(fields)}
                WHERE id = %s
                RETURNING id, name, email, role, plant_id, machines, last_login, created_at;
                """,
                tuple(values),
            )
            user = cur.fetchone()
            conn.commit()

    if not user:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"user": _serialize_user(user)})


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
@require_auth(["superadmin", "admin"])
def delete_user(user_id):
    current_role = g.current_user.get("role")
    current_plant_id = g.current_user.get("plant_id")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if current_role == "superadmin":
                cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
            else:
                cur.execute("DELETE FROM users WHERE id = %s AND plant_id = %s;", (user_id, current_plant_id))
            deleted = cur.rowcount
            conn.commit()

    if not deleted:
        return jsonify({"error": "User not found."}), 404

    return jsonify({"message": "User deleted successfully."})


@app.route("/api/plants/me", methods=["GET"])
@require_auth(["admin"])
def get_my_plant():
    plant_id = g.current_user.get("plant_id")
    if not plant_id:
        return jsonify({"error": "Plant not assigned."}), 400

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, code, status, contact_name, contact_email, contact_phone,
                       location, industry, description, approved_by, approved_at, created_at
                FROM plants
                WHERE id = %s;
                """,
                (plant_id,),
            )
            row = cur.fetchone()
    if not row:
        return jsonify({"error": "Plant not found."}), 404
    return jsonify({"plant": _serialize_plant(row)})


@app.route("/api/plants/me", methods=["PATCH"])
@require_auth(["admin"])
def update_my_plant():
    plant_id = g.current_user.get("plant_id")
    if not plant_id:
        return jsonify({"error": "Plant not assigned."}), 400
    data = request.get_json(silent=True) or {}

    allowed = {"name", "contact_name", "contact_email", "contact_phone", "location", "industry", "description"}
    fields = []
    values = []
    for key in allowed:
        if key in data:
            fields.append(f"{key} = %s")
            values.append((data.get(key) or "").strip() or None)

    if not fields:
        return jsonify({"error": "No valid fields to update."}), 400

    values.append(plant_id)
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                UPDATE plants
                SET {", ".join(fields)}
                WHERE id = %s
                RETURNING id, name, code, status, contact_name, contact_email, contact_phone,
                          location, industry, description, approved_by, approved_at, created_at;
                """,
                tuple(values),
            )
            row = cur.fetchone()
            conn.commit()
    return jsonify({"plant": _serialize_plant(row)})


@app.route("/api/plants", methods=["GET"])
@require_auth(["superadmin"])
def list_plants():
    status = request.args.get("status")
    filters = []
    values = []
    if status:
        filters.append("status = %s")
        values.append(status)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT id, name, code, status, contact_name, contact_email, contact_phone,
                       location, industry, description, approved_by, approved_at, created_at
                FROM plants
                {where_clause}
                ORDER BY created_at DESC;
                """,
                tuple(values),
            )
            rows = cur.fetchall()
    return jsonify({"plants": [_serialize_plant(row) for row in rows]})


@app.route("/api/plants/<int:plant_id>", methods=["PATCH"])
@require_auth(["superadmin"])
def update_plant_by_superadmin(plant_id):
    return jsonify({"error": "Superadmin cannot modify plant information."}), 403


@app.route("/api/plants/<int:plant_id>", methods=["DELETE"])
@require_auth(["superadmin"])
def delete_plant_by_superadmin(plant_id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id, code, name FROM plants WHERE id = %s;", (plant_id,))
            plant = cur.fetchone()
            if not plant:
                return jsonify({"error": "Plant not found."}), 404
            if plant["code"] == "usine-demo":
                return jsonify({"error": "Demo plant cannot be deleted."}), 400

            # Alerts service stores alerts/interventions in the same PostgreSQL database.
            cur.execute(
                """
                DELETE FROM interventions
                WHERE alert_id IN (SELECT id FROM alerts WHERE plant_id = %s);
                """,
                (plant_id,),
            )
            cur.execute("DELETE FROM alerts WHERE plant_id = %s;", (plant_id,))
            cur.execute("DELETE FROM components WHERE plant_id = %s;", (plant_id,))
            cur.execute("DELETE FROM users WHERE plant_id = %s;", (plant_id,))
            cur.execute("DELETE FROM plants WHERE id = %s;", (plant_id,))
            conn.commit()
    return jsonify({"message": "Plant and related data deleted successfully."})


@app.route("/api/plants/<int:plant_id>/overview", methods=["GET"])
@require_auth(["superadmin"])
def get_plant_overview(plant_id):
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, name, code, status, contact_name, contact_email, contact_phone,
                       location, industry, description, approved_by, approved_at, created_at
                FROM plants
                WHERE id = %s;
                """,
                (plant_id,),
            )
            plant = cur.fetchone()
            if not plant:
                return jsonify({"error": "Plant not found."}), 404

            cur.execute(
                """
                SELECT id, name, email, role, plant_id, machines, last_login, created_at
                FROM users
                WHERE plant_id = %s
                ORDER BY role ASC, id ASC;
                """,
                (plant_id,),
            )
            users = cur.fetchall()

            cur.execute("SELECT COUNT(*)::INT AS count FROM users WHERE plant_id = %s;", (plant_id,))
            users_count = cur.fetchone()["count"]
            cur.execute(
                "SELECT COUNT(*)::INT AS count FROM users WHERE plant_id = %s AND role = 'admin';",
                (plant_id,),
            )
            admins_count = cur.fetchone()["count"]
            cur.execute(
                "SELECT COUNT(*)::INT AS count FROM users WHERE plant_id = %s AND role = 'superviseur';",
                (plant_id,),
            )
            supervisors_count = cur.fetchone()["count"]
            cur.execute(
                "SELECT COUNT(*)::INT AS count FROM users WHERE plant_id = %s AND role = 'technicien';",
                (plant_id,),
            )
            technicians_count = cur.fetchone()["count"]
            cur.execute("SELECT COUNT(*)::INT AS count FROM components WHERE plant_id = %s;", (plant_id,))
            components_count = cur.fetchone()["count"]
            cur.execute("SELECT COUNT(*)::INT AS count FROM alerts WHERE plant_id = %s;", (plant_id,))
            total_alerts = cur.fetchone()["count"]
            cur.execute(
                "SELECT COUNT(*)::INT AS count FROM alerts WHERE plant_id = %s AND status != 'resolved';",
                (plant_id,),
            )
            open_alerts = cur.fetchone()["count"]
            cur.execute(
                "SELECT COUNT(*)::INT AS count FROM alerts WHERE plant_id = %s AND status = 'resolved';",
                (plant_id,),
            )
            resolved_alerts = cur.fetchone()["count"]

    return jsonify(
        {
            "plant": _serialize_plant(plant),
            "users": [_serialize_user(user) for user in users],
            "kpis": {
                "users_count": users_count,
                "admins_count": admins_count,
                "supervisors_count": supervisors_count,
                "technicians_count": technicians_count,
                "components_count": components_count,
                "total_alerts": total_alerts,
                "open_alerts": open_alerts,
                "resolved_alerts": resolved_alerts,
            },
        }
    )


@app.route("/api/auth/register-plant", methods=["POST"])
def register_plant():
    data = request.get_json(silent=True) or {}
    plant = data.get("plant") or {}
    users = data.get("users") or {}
    admin_user = users.get("admin") or {}
    supervisor_user = users.get("superviseur") or {}
    technician_user = users.get("technicien") or {}

    plant_name = (plant.get("name") or "").strip()
    plant_code = (plant.get("code") or "").strip().lower()
    contact_name = (plant.get("contact_name") or "").strip()
    contact_email = (plant.get("contact_email") or "").strip().lower()

    if not all([plant_name, plant_code, contact_name, contact_email]):
        return jsonify({"error": "Plant information is incomplete."}), 400
    if not PLANT_CODE_PATTERN.match(plant_code):
        return jsonify({"error": "plant.code must match [a-z0-9-] and be 3-32 chars."}), 400
    required_user_fields = ("name", "email", "password")
    if not all((admin_user.get(field) or "").strip() for field in required_user_fields):
        return jsonify({"error": "Admin user is required (name, email, password)."}), 400

    def _normalize_optional_user(raw_user):
        user = raw_user or {}
        normalized = {
            "name": (user.get("name") or "").strip(),
            "email": (user.get("email") or "").strip().lower(),
            "password": user.get("password") or "",
            "machines": user.get("machines") or [],
        }
        if not normalized["name"] and not normalized["email"] and not normalized["password"]:
            return None
        if not all([normalized["name"], normalized["email"], normalized["password"]]):
            raise ValueError("Optional user must include name, email and password.")
        return normalized

    try:
        normalized_supervisor = _normalize_optional_user(supervisor_user)
        normalized_technician = _normalize_optional_user(technician_user)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    emails = [admin_user.get("email", "").strip().lower(), contact_email]
    if normalized_supervisor:
        emails.append(normalized_supervisor["email"])
    if normalized_technician:
        emails.append(normalized_technician["email"])
    if len(set(emails)) != len(emails):
        return jsonify({"error": "Emails must be distinct in registration payload."}), 400

    payload = {
        "plant": {
            "name": plant_name,
            "code": plant_code,
            "contact_name": contact_name,
            "contact_email": contact_email,
        },
        "users": {
            "admin": {
                "name": admin_user.get("name", "").strip(),
                "email": admin_user.get("email", "").strip().lower(),
                "password": admin_user.get("password", ""),
                "machines": [],
            },
        },
    }
    if normalized_supervisor:
        payload["users"]["superviseur"] = normalized_supervisor
    if normalized_technician:
        payload["users"]["technicien"] = normalized_technician

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM plants WHERE code = %s OR LOWER(name) = LOWER(%s);", (plant_code, plant_name))
            if cur.fetchone():
                return jsonify({"error": "Plant already exists."}), 409
            cur.execute(
                """
                SELECT id FROM plant_registrations
                WHERE status = 'pending' AND (plant_code = %s OR LOWER(plant_name) = LOWER(%s));
                """,
                (plant_code, plant_name),
            )
            if cur.fetchone():
                return jsonify({"error": "A pending registration already exists for this plant."}), 409
            cur.execute(
                """
                SELECT id FROM users WHERE LOWER(email) = ANY(%s);
                """,
                (emails,),
            )
            if cur.fetchone():
                return jsonify({"error": "One or more emails already exist."}), 409

            cur.execute(
                """
                INSERT INTO plant_registrations (
                    plant_name, plant_code, contact_name, contact_email, payload, status
                )
                VALUES (%s, %s, %s, %s, %s, 'pending')
                RETURNING id, plant_name, plant_code, status, created_at;
                """,
                (plant_name, plant_code, contact_name, contact_email, Json(payload)),
            )
            registration = cur.fetchone()
            conn.commit()

    return jsonify({"registration": registration}), 201


@app.route("/api/auth/registrations", methods=["GET"])
@require_auth(["superadmin"])
def list_registrations():
    status = request.args.get("status", "pending")
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if status == "all":
                cur.execute(
                    """
                    SELECT id, plant_name, plant_code, contact_name, contact_email, status,
                           review_note, reviewed_by, reviewed_at, created_at, payload
                    FROM plant_registrations
                    ORDER BY created_at DESC;
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, plant_name, plant_code, contact_name, contact_email, status,
                           review_note, reviewed_by, reviewed_at, created_at, payload
                    FROM plant_registrations
                    WHERE status = %s
                    ORDER BY created_at DESC;
                    """,
                    (status,),
                )
            rows = cur.fetchall()
    return jsonify({"registrations": rows})


@app.route("/api/auth/registrations/<int:registration_id>/review", methods=["PATCH"])
@require_auth(["superadmin"])
def review_registration(registration_id):
    data = request.get_json(silent=True) or {}
    action = (data.get("action") or "").strip().lower()
    review_note = (data.get("note") or "").strip() or None
    reviewer_id = int(g.current_user.get("sub"))

    if action not in {"approve", "reject"}:
        return jsonify({"error": "action must be approve or reject."}), 400

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, plant_name, plant_code, payload, status
                FROM plant_registrations
                WHERE id = %s;
                """,
                (registration_id,),
            )
            registration = cur.fetchone()
            if not registration:
                return jsonify({"error": "Registration not found."}), 404
            if registration["status"] != "pending":
                return jsonify({"error": "Registration already reviewed."}), 400

            if action == "reject":
                cur.execute(
                    """
                    UPDATE plant_registrations
                    SET status = 'rejected', review_note = %s, reviewed_by = %s, reviewed_at = NOW()
                    WHERE id = %s
                    RETURNING id, status, review_note, reviewed_at;
                    """,
                    (review_note, reviewer_id, registration_id),
                )
                reviewed = cur.fetchone()
                conn.commit()
                return jsonify({"registration": reviewed})

            payload = registration["payload"] or {}
            plant_payload = payload.get("plant") or {}
            users_payload = payload.get("users") or {}
            admin_payload = users_payload.get("admin") or {}

            cur.execute(
                """
                INSERT INTO plants (
                    name, code, status, contact_name, contact_email, approved_by, approved_at
                )
                VALUES (%s, %s, 'active', %s, %s, %s, NOW())
                RETURNING id, name, code;
                """,
                (
                    plant_payload.get("name"),
                    plant_payload.get("code"),
                    plant_payload.get("contact_name"),
                    plant_payload.get("contact_email"),
                    reviewer_id,
                ),
            )
            plant = cur.fetchone()

            for role_key in ("admin", "superviseur", "technicien"):
                user_payload = users_payload.get(role_key)
                if not user_payload:
                    continue
                password_hash = bcrypt.hashpw(
                    user_payload.get("password", "").encode("utf-8"),
                    bcrypt.gensalt(),
                ).decode("utf-8")
                cur.execute(
                    """
                    INSERT INTO users (name, email, password_hash, role, plant_id, machines)
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (
                        user_payload.get("name"),
                        user_payload.get("email"),
                        password_hash,
                        role_key,
                        plant["id"],
                        user_payload.get("machines") or [],
                    ),
                )

            cur.execute(
                """
                UPDATE plant_registrations
                SET status = 'approved', review_note = %s, reviewed_by = %s, reviewed_at = NOW()
                WHERE id = %s
                RETURNING id, status, review_note, reviewed_at;
                """,
                (review_note, reviewer_id, registration_id),
            )
            reviewed = cur.fetchone()
            conn.commit()

    # Email sending should not break the approval flow.
    recipients = []
    contact_email = plant_payload.get("contact_email")
    if contact_email:
        recipients.append(
            (
                contact_email,
                plant_payload.get("contact_name") or "Responsable usine",
            )
        )
    admin_email = admin_payload.get("email")
    if admin_email and admin_email != contact_email:
        recipients.append((admin_email, admin_payload.get("name") or "Admin usine"))

    for recipient_email, recipient_name in recipients:
        try:
            send_registration_approved_email(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                plant_name=plant_payload.get("name") or registration["plant_name"],
                plant_code=plant_payload.get("code") or registration["plant_code"],
            )
        except Exception as exc:
            app.logger.exception("Failed to send approval email to %s: %s", recipient_email, exc)

    return jsonify({"registration": reviewed, "plant": plant})


@app.route("/api/components", methods=["GET"])
@require_auth(["superadmin", "admin", "superviseur", "technicien"])
def list_components():
    current_role = g.current_user.get("role")
    current_plant_id = g.current_user.get("plant_id")
    plant_id = request.args.get("plant_id")

    filters = []
    values = []
    if current_role == "superadmin":
        if plant_id:
            filters.append("plant_id = %s")
            values.append(int(plant_id))
    else:
        filters.append("plant_id = %s")
        values.append(current_plant_id)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT id, key, name, type, plant_id, enabled, created_at, updated_at
                FROM components
                {where_clause}
                ORDER BY id ASC;
                """,
                tuple(values),
            )
            rows = cur.fetchall()
    return jsonify({"components": [_serialize_component(row) for row in rows]})


@app.route("/api/components", methods=["POST"])
@require_auth(["superadmin", "admin"])
def create_component():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    component_type = (data.get("type") or "").strip().lower()
    enabled = bool(data.get("enabled", True))
    current_role = g.current_user.get("role")
    current_plant_id = g.current_user.get("plant_id")
    component_plant_id = data.get("plant_id")

    if not name or not component_type:
        return jsonify({"error": "name and type are required."}), 400
    if component_type not in COMPONENT_TYPES:
        return jsonify({"error": "Invalid component type."}), 400

    safe_name = "".join(ch for ch in name.lower() if ch.isalnum())
    if not safe_name:
        safe_name = "component"
    key = f"{safe_name}-{int(datetime.now(timezone.utc).timestamp())}"
    if current_role == "superadmin":
        if not component_plant_id:
            return jsonify({"error": "plant_id is required for superadmin component creation."}), 400
        target_plant_id = component_plant_id
    else:
        target_plant_id = current_plant_id

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO components (key, name, type, plant_id, enabled)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, key, name, type, plant_id, enabled, created_at, updated_at;
                    """,
                    (key, name, component_type, target_plant_id, enabled),
                )
                row = cur.fetchone()
                conn.commit()
            except errors.UniqueViolation:
                conn.rollback()
                return jsonify({"error": "Component key already exists."}), 409

    return jsonify({"component": _serialize_component(row)}), 201


@app.route("/api/components/<int:component_id>", methods=["PATCH"])
@require_auth(["superadmin", "admin"])
def update_component(component_id):
    data = request.get_json(silent=True) or {}
    current_role = g.current_user.get("role")
    current_plant_id = g.current_user.get("plant_id")
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
    if "plant_id" in data:
        if current_role != "superadmin":
            return jsonify({"error": "Only superadmin can change component plant."}), 403
        fields.append("plant_id = %s")
        values.append(data.get("plant_id"))

    if not fields:
        return jsonify({"error": "No valid fields to update."}), 400

    fields.append("updated_at = NOW()")
    values.append(component_id)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                if current_role != "superadmin":
                    cur.execute(
                        "SELECT id FROM components WHERE id = %s AND plant_id = %s;",
                        (component_id, current_plant_id),
                    )
                    if not cur.fetchone():
                        return jsonify({"error": "Component not found."}), 404
                cur.execute(
                    f"""
                    UPDATE components
                    SET {", ".join(fields)}
                    WHERE id = %s
                    RETURNING id, key, name, type, plant_id, enabled, created_at, updated_at;
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
@require_auth(["superadmin", "admin"])
def delete_component(component_id):
    current_role = g.current_user.get("role")
    current_plant_id = g.current_user.get("plant_id")
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if current_role == "superadmin":
                cur.execute("DELETE FROM components WHERE id = %s;", (component_id,))
            else:
                cur.execute("DELETE FROM components WHERE id = %s AND plant_id = %s;", (component_id, current_plant_id))
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
