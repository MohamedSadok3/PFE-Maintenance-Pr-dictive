import eventlet
eventlet.monkey_patch()

import json
import os
import threading
from datetime import datetime, timedelta, timezone
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
                    machine TEXT NOT NULL,
                    defect TEXT NOT NULL,
                    anomaly_score DOUBLE PRECISION NOT NULL,
                    confidence DOUBLE PRECISION NOT NULL,
                    severity TEXT NOT NULL,
                    status TEXT DEFAULT 'open',
                    assigned_to INT NULL,
                    acknowledged BOOL DEFAULT false,
                    created_at TIMESTAMP NOT NULL,
                    resolved_at TIMESTAMP NULL
                );
                """
            )
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
            conn.commit()


def severity_from_score(score):
    if score >= 0.85:
        return "Critique"
    if score >= 0.65:
        return "Majeure"
    if score >= 0.40:
        return "Mineure"
    return None


def insert_alert(machine, defect, defect_score, confidence, severity):
    created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO alerts (
                    machine, defect, anomaly_score, confidence, severity, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, machine, defect, anomaly_score, confidence, severity,
                          status, assigned_to, acknowledged, created_at, resolved_at;
                """,
                (machine, defect, defect_score, confidence, severity, created_at),
            )
            alert = cur.fetchone()
            conn.commit()
            return alert


def serialize_alert(alert):
    return {
        "id": alert["id"],
        "machine": alert["machine"],
        "defect": alert["defect"],
        "defect_score": float(alert["anomaly_score"]),
        "anomaly_score": float(alert["anomaly_score"]),
        "confidence": float(alert["confidence"]),
        "severity": alert["severity"],
        "status": alert["status"],
        "assigned_to": alert["assigned_to"],
        "acknowledged": bool(alert["acknowledged"]),
        "created_at": alert["created_at"].isoformat() if alert["created_at"] else None,
        "resolved_at": alert["resolved_at"].isoformat() if alert["resolved_at"] else None,
    }


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

            alert = insert_alert(
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
    machine = request.args.get("machine")
    severity = request.args.get("severity")
    status = request.args.get("status")
    page = max(1, int(request.args.get("page", 1)))
    limit = max(1, int(request.args.get("limit", 20)))
    offset = (page - 1) * limit

    filters = []
    values = []

    if machine:
        filters.append("machine = %s")
        values.append(machine)
    if severity:
        filters.append("severity = %s")
        values.append(severity)
    if status:
        filters.append("status = %s")
        values.append(status)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    values.extend([limit, offset])

    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"""
                SELECT id, machine, defect, anomaly_score, confidence, severity,
                       status, assigned_to, acknowledged, created_at, resolved_at
                FROM alerts
                {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s;
                """,
                tuple(values),
            )
            rows = cur.fetchall()

    return jsonify({"alerts": [serialize_alert(row) for row in rows], "page": page, "limit": limit})


@app.route("/api/alertes/<int:alert_id>", methods=["PATCH"])
def patch_alerte(alert_id):
    data = request.get_json(silent=True) or {}
    fields = []
    values = []

    if "status" in data:
        fields.append("status = %s")
        values.append(data["status"])
        if data["status"] == "resolved":
            fields.append("resolved_at = %s")
            values.append(datetime.now(timezone.utc).replace(tzinfo=None))
    assigned_to_in_payload = "assigned_to" in data

    if assigned_to_in_payload:
        fields.append("assigned_to = %s")
        values.append(data["assigned_to"])
        if data["assigned_to"] is not None:
            fields.append("status = %s")
            values.append("assigned")
    if "acknowledged" in data:
        fields.append("acknowledged = %s")
        values.append(bool(data["acknowledged"]))

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
                RETURNING id, machine, defect, anomaly_score, confidence, severity,
                          status, assigned_to, acknowledged, created_at, resolved_at;
                """,
                tuple(values),
            )
            row = cur.fetchone()

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
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT COUNT(*)::INT AS count FROM alerts WHERE status = 'open';")
            open_alerts = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT COUNT(*)::INT AS count
                FROM interventions i
                JOIN alerts a ON a.id = i.alert_id
                WHERE a.status != 'resolved';
                """
            )
            pending_interventions = cur.fetchone()["count"]

            cur.execute(
                """
                SELECT id, machine, defect, anomaly_score, confidence, severity,
                       status, assigned_to, acknowledged, created_at, resolved_at
                FROM alerts
                ORDER BY created_at DESC
                LIMIT 5;
                """
            )
            recent_alerts = [serialize_alert(row) for row in cur.fetchall()]

            cur.execute(
                """
                SELECT id, machine, defect, anomaly_score, confidence, severity,
                       status, assigned_to, acknowledged, created_at, resolved_at
                FROM alerts
                WHERE status = 'open'
                ORDER BY severity DESC, created_at DESC
                LIMIT 5;
                """
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
