import eventlet
eventlet.monkey_patch()

import json
import os
import threading
from datetime import datetime, timedelta, timezone
import jwt
import psycopg2
import redis
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from psycopg2.extras import RealDictCursor
load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
POSTGRES_URL = os.environ.get("POSTGRES_URL")
JWT_SECRET = os.environ.get("JWT_SECRET", "supersecretkey123")
PORT = 5003
PREDICTIONS_CHANNEL = "ml_predictions"

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def get_db_connection():
    if not POSTGRES_URL:
        raise RuntimeError("POSTGRES_URL is not configured.")
    return psycopg2.connect(POSTGRES_URL)


def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    plant_id INT NULL,
                    machine TEXT NOT NULL,
                    defect TEXT NOT NULL,
                    anomaly_score DOUBLE PRECISION NOT NULL,
                    confidence DOUBLE PRECISION NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    assigned_to INT NULL,
                    assigned_by INT NULL,
                    acknowledged BOOL DEFAULT false,
                    created_at TIMESTAMP NOT NULL,
                    resolved_at TIMESTAMP NULL
                );
                """
            )
            cur.execute("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS plant_id INT NULL;")
            cur.execute("ALTER TABLE alerts ADD COLUMN IF NOT EXISTS assigned_by INT NULL;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS interventions (
                    id SERIAL PRIMARY KEY,
                    alert_id INT REFERENCES alerts(id) ON DELETE CASCADE,
                    machine TEXT NOT NULL,
                    assigned_to INT NULL,
                    deadline TIMESTAMP NULL,
                    notes TEXT NULL,
                    created_at TIMESTAMP NOT NULL
                );
                """
            )
            cur.execute(
                """
                UPDATE alerts
                SET plant_id = (
                    SELECT id FROM plants ORDER BY id ASC LIMIT 1
                )
                WHERE plant_id IS NULL;
                """
            )
            conn.commit()


def get_default_plant_id(cur):
    cur.execute("SELECT id FROM plants ORDER BY id ASC LIMIT 1;")
    row = cur.fetchone()
    return row["id"] if row else None


def severity_from_score(score):
    if score >= 0.85:
        return "Critique"
    if score >= 0.65:
        return "Majeure"
    if score >= 0.40:
        return "Mineure"
    return None


def insert_alert(plant_id, machine, defect, defect_score, confidence, severity):
    created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO alerts (
                    plant_id, machine, defect, anomaly_score, confidence, severity, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, plant_id, machine, defect, anomaly_score, confidence, severity,
                          status, assigned_to, assigned_by, acknowledged, created_at, resolved_at,
                          NULL::TEXT AS assigned_to_name, NULL::TEXT AS assigned_by_name;
                """,
                (plant_id, machine, defect, defect_score, confidence, severity, created_at),
            )
            alert = cur.fetchone()
            conn.commit()
            return alert


def serialize_alert(alert):
    return {
        "id": alert["id"],
        "plant_id": alert.get("plant_id"),
        "machine": alert["machine"],
        "defect": alert["defect"],
        "defect_score": float(alert["anomaly_score"]),
        "anomaly_score": float(alert["anomaly_score"]),
        "confidence": float(alert["confidence"]),
        "severity": alert["severity"],
        "status": alert["status"],
        "assigned_to": alert["assigned_to"],
        "assigned_to_name": alert.get("assigned_to_name"),
        "assigned_by": alert["assigned_by"],
        "assigned_by_name": alert.get("assigned_by_name"),
        "acknowledged": bool(alert["acknowledged"]),
        "created_at": alert["created_at"].isoformat() if alert["created_at"] else None,
        "resolved_at": alert["resolved_at"].isoformat() if alert["resolved_at"] else None,
        "validation_at": alert["resolved_at"].isoformat() if alert["resolved_at"] else None,
    }


def get_current_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None


def get_alert_by_id(cur, alert_id):
    cur.execute(
        """
        SELECT id, machine, defect, anomaly_score, confidence, severity,
               plant_id, status, assigned_to, assigned_by, acknowledged, created_at, resolved_at
        FROM alerts
        WHERE id = %s;
        """,
        (alert_id,),
    )
    return cur.fetchone()


def get_alert_with_users(cur, alert_id):
    cur.execute(
        """
        SELECT a.id, a.machine, a.defect, a.anomaly_score, a.confidence, a.severity,
               a.plant_id, a.status, a.assigned_to, a.assigned_by, a.acknowledged, a.created_at, a.resolved_at,
               assigned_user.name AS assigned_to_name,
               assigner_user.name AS assigned_by_name
        FROM alerts a
        LEFT JOIN users assigned_user ON assigned_user.id = a.assigned_to
        LEFT JOIN users assigner_user ON assigner_user.id = a.assigned_by
        WHERE a.id = %s;
        """,
        (alert_id,),
    )
    return cur.fetchone()


def get_technician(cur, user_id):
    cur.execute(
        """
        SELECT id, role, machines
               , plant_id
        FROM users
        WHERE id = %s;
        """,
        (user_id,),
    )
    return cur.fetchone()


def consume_predictions():
    pubsub = redis_client.pubsub()
    pubsub.subscribe(PREDICTIONS_CHANNEL)

    for message in pubsub.listen():
        if message.get("type") != "message":
            continue

        try:
            prediction = json.loads(message.get("data", "{}"))
            defect_scores = prediction.get("defect_scores") or {}
            if isinstance(defect_scores, dict) and defect_scores:
                top_defect, top_score = max(defect_scores.items(), key=lambda item: float(item[1]))
                score = float(top_score)
                defect_name = top_defect
            else:
                score = float(prediction.get("defect_score", prediction.get("anomaly_score", 0)))
                defect_name = prediction.get("defect", "anomaly_detected")
            severity = severity_from_score(score)

            # Always emit raw prediction for live charts.
            socketio.emit("sensor:data", prediction)

            if not severity:
                continue

            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    incoming_plant_id = prediction.get("plant_id")
                    if incoming_plant_id:
                        plant_id = int(incoming_plant_id)
                    else:
                        plant_id = get_default_plant_id(cur)
            if not plant_id:
                continue

            alert = insert_alert(
                plant_id=plant_id,
                machine=prediction.get("machine", "unknown"),
                defect=defect_name,
                defect_score=score,
                confidence=float(prediction.get("confidence", 0)),
                severity=severity,
            )
            socketio.emit("alert:new", serialize_alert(alert))
        except Exception:
            continue


@app.route("/api/alertes", methods=["GET"])
def list_alertes():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    machine = request.args.get("machine")
    severity = request.args.get("severity")
    status = request.args.get("status")
    acknowledged = request.args.get("acknowledged")
    page = max(1, int(request.args.get("page", 1)))
    limit = max(1, int(request.args.get("limit", 20)))
    offset = (page - 1) * limit
    current_role = current_user.get("role")
    current_plant_id = current_user.get("plant_id")

    filters = []
    values = []

    if current_role != "superadmin":
        filters.append("a.plant_id = %s")
        values.append(current_plant_id)
    if machine:
        filters.append("a.machine = %s")
        values.append(machine)
    if severity:
        filters.append("a.severity = %s")
        values.append(severity)
    if status:
        filters.append("a.status = %s")
        values.append(status)
    if acknowledged is not None:
        acknowledged_value = acknowledged.lower()
        if acknowledged_value not in {"true", "false"}:
            return jsonify({"error": "acknowledged must be true or false."}), 400
        filters.append("a.acknowledged = %s")
        values.append(acknowledged_value == "true")
    if current_role == "technicien":
        filters.append("a.assigned_to = %s")
        values.append(int(current_user.get("sub")))

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    values.extend([limit, offset])

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT a.id, a.machine, a.defect, a.anomaly_score, a.confidence, a.severity,
                       a.plant_id, a.status, a.assigned_to, a.assigned_by, a.acknowledged, a.created_at, a.resolved_at,
                       assigned_user.name AS assigned_to_name,
                       assigner_user.name AS assigned_by_name
                FROM alerts a
                LEFT JOIN users assigned_user ON assigned_user.id = a.assigned_to
                LEFT JOIN users assigner_user ON assigner_user.id = a.assigned_by
                {where_clause}
                ORDER BY a.created_at DESC
                LIMIT %s OFFSET %s;
                """,
                tuple(values),
            )
            rows = cur.fetchall()

    return jsonify({"alerts": [serialize_alert(row) for row in rows], "page": page, "limit": limit})


@app.route("/api/alertes/<int:alert_id>", methods=["GET"])
def get_alerte(alert_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            row = get_alert_with_users(cur, alert_id)
            if not row:
                return jsonify({"error": "Alert not found."}), 404
            if current_user.get("role") != "superadmin" and row["plant_id"] != current_user.get("plant_id"):
                return jsonify({"error": "Forbidden"}), 403

            if current_user.get("role") == "technicien" and row["assigned_to"] != int(current_user.get("sub")):
                return jsonify({"error": "Forbidden"}), 403

    return jsonify({"alert": serialize_alert(row)})


@app.route("/api/alertes/<int:alert_id>", methods=["PATCH"])
def patch_alerte(alert_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    current_role = current_user.get("role")
    current_user_id = int(current_user.get("sub"))
    current_plant_id = current_user.get("plant_id")
    data = request.get_json(silent=True) or {}
    fields = []
    values = []
    assigned_to_in_payload = "assigned_to" in data
    acknowledged_in_payload = "acknowledged" in data
    status_in_payload = "status" in data

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            current_alert = get_alert_by_id(cur, alert_id)
            if not current_alert:
                return jsonify({"error": "Alert not found."}), 404
            if current_role != "superadmin" and current_alert["plant_id"] != current_plant_id:
                return jsonify({"error": "Forbidden"}), 403

            if status_in_payload:
                if current_role not in {"admin", "superviseur"}:
                    return jsonify({"error": "Only supervisor/admin can validate a task."}), 403
                if data["status"] == "resolved":
                    if not current_alert["acknowledged"] or current_alert["status"] != "acknowledged":
                        return jsonify(
                            {"error": "Task must be acquitted by the assigned technician before validation."}
                        ), 400
                elif data["status"] == "reopened":
                    if current_alert["status"] != "resolved":
                        return jsonify({"error": "Only validated tasks can be reopened."}), 400
                else:
                    return jsonify({"error": "Only status=resolved or status=reopened are supported."}), 400

            if assigned_to_in_payload:
                if current_role not in {"admin", "superviseur"}:
                    return jsonify({"error": "Only supervisor/admin can assign tasks."}), 403
                if data["assigned_to"] is not None:
                    technician = get_technician(cur, data["assigned_to"])
                    if not technician or technician["role"] != "technicien":
                        return jsonify({"error": "Assigned user must be a technician."}), 400
                    if current_role != "superadmin" and technician["plant_id"] != current_plant_id:
                        return jsonify({"error": "Technician does not belong to your plant."}), 400
                    technician_machines = technician["machines"] or []
                    if current_alert["machine"] not in technician_machines:
                        return jsonify(
                            {
                                "error": "Technician is not assigned to this machine type.",
                            }
                        ), 400

            if acknowledged_in_payload:
                if current_role != "technicien":
                    return jsonify({"error": "Only assigned technician can acquit task."}), 403
                if current_alert["assigned_to"] != current_user_id:
                    return jsonify({"error": "You are not assigned to this task."}), 403
                if bool(data["acknowledged"]) is not True:
                    return jsonify({"error": "Only acknowledged=true is supported."}), 400

    if status_in_payload:
        if data["status"] == "resolved":
            fields.append("status = %s")
            values.append("resolved")
            fields.append("acknowledged = %s")
            values.append(True)
            fields.append("resolved_at = %s")
            values.append(datetime.now(timezone.utc).replace(tzinfo=None))
        elif data["status"] == "reopened":
            reopened_status = "assigned" if current_alert["assigned_to"] is not None else "open"
            fields.append("status = %s")
            values.append(reopened_status)
            fields.append("acknowledged = %s")
            values.append(False)
            fields.append("resolved_at = %s")
            values.append(None)

    if assigned_to_in_payload:
        fields.append("assigned_to = %s")
        values.append(data["assigned_to"])
        if data["assigned_to"] is not None:
            fields.append("assigned_by = %s")
            values.append(current_user_id)
            fields.append("status = %s")
            values.append("assigned")
            fields.append("acknowledged = %s")
            values.append(False)
        else:
            fields.append("assigned_by = %s")
            values.append(None)
    if "acknowledged" in data:
        fields.append("acknowledged = %s")
        values.append(bool(data["acknowledged"]))
        fields.append("status = %s")
        values.append("acknowledged")

    if not fields:
        return jsonify({"error": "No fields to update."}), 400

    values.append(alert_id)

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                UPDATE alerts
                SET {", ".join(fields)}
                WHERE id = %s
                RETURNING id;
                """,
                tuple(values),
            )
            row = cur.fetchone()
            if row:
                row = get_alert_with_users(cur, alert_id)

            if row and assigned_to_in_payload:
                cur.execute(
                    """
                    SELECT id
                    FROM interventions
                    WHERE alert_id = %s
                    ORDER BY id DESC
                    LIMIT 1;
                    """,
                    (alert_id,),
                )
                intervention = cur.fetchone()
                if row["assigned_to"] is not None:
                    deadline = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
                    if intervention:
                        cur.execute(
                            """
                            UPDATE interventions
                            SET assigned_to = %s, deadline = %s
                            WHERE id = %s;
                            """,
                            (row["assigned_to"], deadline, intervention["id"]),
                        )
                    else:
                        cur.execute(
                            """
                            INSERT INTO interventions (alert_id, machine, assigned_to, deadline, created_at)
                            VALUES (%s, %s, %s, %s, %s);
                            """,
                            (
                                alert_id,
                                row["machine"],
                                row["assigned_to"],
                                deadline,
                                datetime.now(timezone.utc).replace(tzinfo=None),
                            ),
                        )
            conn.commit()

    if not row:
        return jsonify({"error": "Alert not found."}), 404

    serialized = serialize_alert(row)
    socketio.emit("alert:updated", serialized)
    return jsonify({"alert": serialized})


@app.route("/api/dashboard/summary", methods=["GET"])
def dashboard_summary():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401
    current_role = current_user.get("role")
    current_plant_id = current_user.get("plant_id")

    filters = []
    values = []
    if current_role != "superadmin":
        filters.append("a.plant_id = %s")
        values.append(current_plant_id)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT COUNT(*)::INT AS count
                FROM alerts a
                {where_clause} {"AND" if where_clause else "WHERE"} a.status = 'open';
                """,
                tuple(values),
            )
            open_alerts = cur.fetchone()["count"]

            cur.execute(
                f"""
                SELECT COUNT(*)::INT AS count
                FROM interventions i
                JOIN alerts a ON a.id = i.alert_id
                {where_clause} {"AND" if where_clause else "WHERE"} a.status != 'resolved';
                """,
                tuple(values),
            )
            pending_interventions = cur.fetchone()["count"]

            cur.execute(
                f"""
                SELECT a.id, a.machine, a.defect, a.anomaly_score, a.confidence, a.severity,
                       a.plant_id, a.status, a.assigned_to, a.assigned_by, a.acknowledged, a.created_at, a.resolved_at,
                       assigned_user.name AS assigned_to_name,
                       assigner_user.name AS assigned_by_name
                FROM alerts a
                LEFT JOIN users assigned_user ON assigned_user.id = a.assigned_to
                LEFT JOIN users assigner_user ON assigner_user.id = a.assigned_by
                {where_clause}
                ORDER BY a.created_at DESC
                LIMIT 5;
                """,
                tuple(values),
            )
            recent_alerts = [serialize_alert(row) for row in cur.fetchall()]

            cur.execute(
                f"""
                SELECT a.id, a.machine, a.defect, a.anomaly_score, a.confidence, a.severity,
                       a.plant_id, a.status, a.assigned_to, a.assigned_by, a.acknowledged, a.created_at, a.resolved_at,
                       assigned_user.name AS assigned_to_name,
                       assigner_user.name AS assigned_by_name
                FROM alerts a
                LEFT JOIN users assigned_user ON assigned_user.id = a.assigned_to
                LEFT JOIN users assigner_user ON assigner_user.id = a.assigned_by
                {where_clause} {"AND" if where_clause else "WHERE"} a.status = 'open'
                ORDER BY a.severity DESC, a.created_at DESC
                LIMIT 5;
                """,
                tuple(values),
            )
            pending_list = [serialize_alert(row) for row in cur.fetchall()]

    return jsonify(
        {
            "active_machines": 4,
            "open_alerts": open_alerts,
            "pending_interventions": pending_interventions,
            "recent_alerts": recent_alerts,
            "pending_list": pending_list,
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "alertes"})


init_db()
consumer_thread = threading.Thread(target=consume_predictions, daemon=True)
consumer_thread.start()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=PORT, debug=False)
