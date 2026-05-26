from datetime import datetime, timedelta, timezone
import json
import redis
from flask_socketio import SocketIO

from shared.config import get_env
from shared.database import get_db_connection
from shared.rows import row_to_dict, rows_to_dicts
from queries import (
    ALERTS_CREATE_TABLE,
    ALERTS_ADD_COLUMN_PLANT_ID,
    ALERTS_ADD_COLUMN_ASSIGNED_BY,
    INTERVENTIONS_CREATE_TABLE,
    ALERTS_BACKFILL_PLANT_ID,
    ALERT_SELECT_DEFAULT_PLANT,
    ALERT_INSERT,
    ALERT_SELECT_BY_ID,
    ALERT_SELECT_WITH_USERS,
    TECHNICIAN_SELECT_BY_ID,
    ALERT_SELECT_LIST,
    ALERT_UPDATE,
    INTERVENTION_SELECT_LATEST_FOR_ALERT,
    INTERVENTION_UPDATE,
    INTERVENTION_INSERT,
    DASHBOARD_COUNT_OPEN_ALERTS,
    DASHBOARD_COUNT_PENDING_INTERVENTIONS,
    DASHBOARD_SELECT_RECENT_ALERTS,
    DASHBOARD_SELECT_PENDING_LIST,
)


class AlertService:
    def __init__(self):
        self.redis_client = redis.from_url(get_env("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

    def init_db(self):
        """Initialize database tables for alerts service."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(ALERTS_CREATE_TABLE)
                cur.execute(ALERTS_ADD_COLUMN_PLANT_ID)
                cur.execute(ALERTS_ADD_COLUMN_ASSIGNED_BY)
                cur.execute(INTERVENTIONS_CREATE_TABLE)
                cur.execute(ALERTS_BACKFILL_PLANT_ID)
                conn.commit()

    def get_default_plant_id(self):
        """Get the default plant ID for alerts without plant_id."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(ALERT_SELECT_DEFAULT_PLANT)
                row = cur.fetchone()
                return row[0] if row else None

    def severity_from_score(self, score):
        """Determine severity level from anomaly score."""
        if score >= 0.85:
            return "Critique"
        if score >= 0.65:
            return "Majeure"
        if score >= 0.40:
            return "Mineure"
        return None

    def insert_alert(self, plant_id, machine, defect, defect_score, confidence, severity):
        """Insert a new alert into the database and return Alert model."""
        created_at = datetime.now(timezone.utc).replace(tzinfo=None)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    ALERT_INSERT,
                    (plant_id, machine, defect, defect_score, confidence, severity, created_at),
                )
                row = cur.fetchone()
                conn.commit()
                return row_to_dict(row)

    def get_alert_by_id(self, alert_id):
        """Get alert by ID."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(ALERT_SELECT_BY_ID, (alert_id,))
                row = cur.fetchone()
                return row_to_dict(row)

    def get_alert_with_users(self, alert_id):
        """Get alert with assigned user names (returns enriched dict due to joins)."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(ALERT_SELECT_WITH_USERS, (alert_id,))
                row = cur.fetchone()
                return row_to_dict(row)

    def get_technician(self, user_id):
        """Get technician information (returns dict for partial user data)."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(TECHNICIAN_SELECT_BY_ID, (user_id,))
                row = cur.fetchone()
                return row_to_dict(row)

    def list_alerts(self, current_user, filters=None):
        """List alerts with role-based filtering (returns enriched dicts due to joins)."""
        filters = filters or {}
        machine = filters.get("machine")
        severity = filters.get("severity")
        status = filters.get("status")
        acknowledged = filters.get("acknowledged")
        page = max(1, int(filters.get("page", 1)))
        limit = max(1, int(filters.get("limit", 20)))
        offset = (page - 1) * limit

        current_role = current_user.get("role")
        current_plant_id = current_user.get("plant_id")

        query_filters = []
        values = []

        if current_role != "superadmin":
            query_filters.append("a.plant_id = %s")
            values.append(current_plant_id)
        if machine:
            query_filters.append("a.machine = %s")
            values.append(machine)
        if severity:
            query_filters.append("a.severity = %s")
            values.append(severity)
        if status:
            query_filters.append("a.status = %s")
            values.append(status)
        if acknowledged is not None:
            acknowledged_value = acknowledged.lower()
            if acknowledged_value not in {"true", "false"}:
                raise ValueError("Le paramètre acknowledged doit être true ou false.")
            query_filters.append("a.acknowledged = %s")
            values.append(acknowledged_value == "true")
        if current_role == "technicien":
            query_filters.append("a.assigned_to = %s")
            values.append(int(current_user.get("sub")))

        where_clause = f"WHERE {' AND '.join(query_filters)}" if query_filters else ""
        values.extend([limit, offset])

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    ALERT_SELECT_LIST.format(where_clause=where_clause),
                    tuple(values),
                )
                rows = cur.fetchall()

        return rows_to_dicts(rows), page, limit

    def update_alert(self, alert_id, data, current_user):
        """Update alert with validation. Returns dict with enriched user data."""
        current_role = current_user.get("role")
        current_user_id = int(current_user.get("sub"))
        current_plant_id = current_user.get("plant_id")

        fields = []
        values = []
        assigned_to_in_payload = "assigned_to" in data
        acknowledged_in_payload = "acknowledged" in data
        status_in_payload = "status" in data

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                current_alert = self.get_alert_by_id(alert_id)
                if not current_alert:
                    return None, "Alerte introuvable."
                if current_role != "superadmin" and current_alert["plant_id"] != current_plant_id:
                    return None, "Accès refusé."

                # Validate status changes
                if status_in_payload:
                    if current_role not in {"admin", "superviseur"}:
                        return None, "Seul un superviseur ou administrateur peut valider une tâche."
                    if data["status"] == "resolved":
                        if not current_alert["acknowledged"] or current_alert["status"] != "acknowledged":
                            return None, "La tâche doit être acquittée par le technicien assigné avant validation."
                    elif data["status"] == "reopened":
                        if current_alert["status"] != "resolved":
                            return None, "Seules les tâches validées peuvent être réouvertes."
                    else:
                        return None, "Seuls les statuts 'resolved' ou 'reopened' sont supportés."

                # Validate assignment
                if assigned_to_in_payload:
                    if current_role not in {"admin", "superviseur"}:
                        return None, "Seul un superviseur ou administrateur peut assigner des tâches."
                    if data["assigned_to"] is not None:
                        technician = self.get_technician(data["assigned_to"])
                        if not technician or technician["role"] != "technicien":
                            return None, "L'utilisateur assigné doit être un technicien."
                        if current_role != "superadmin" and technician["plant_id"] != current_plant_id:
                            return None, "Ce technicien n'appartient pas à votre usine."
                        technician_machines = technician["machines"] or []
                        if current_alert["machine"] not in technician_machines:
                            return None, "Ce technicien n'est pas assigné à ce type de machine."

                # Validate acknowledgment
                if acknowledged_in_payload:
                    if current_role != "technicien":
                        return None, "Seul le technicien assigné peut acquitter une tâche."
                    if current_alert["assigned_to"] != current_user_id:
                        return None, "Vous n'êtes pas assigné à cette tâche."
                    if bool(data["acknowledged"]) is not True:
                        return None, "Seul acknowledged=true est supporté."

                # Build update fields
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
                    return None, "Aucun champ à mettre à jour."

                values.append(alert_id)

                cur.execute(
                    ALERT_UPDATE.format(fields=", ".join(fields)),
                    tuple(values),
                )
                row = cur.fetchone()
                if row:
                    row = self.get_alert_with_users(alert_id)

                # Handle interventions
                if row and assigned_to_in_payload:
                    cur.execute(INTERVENTION_SELECT_LATEST_FOR_ALERT, (alert_id,))
                    intervention = cur.fetchone()
                    if row["assigned_to"] is not None:
                        deadline = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24)
                        if intervention:
                            cur.execute(
                                INTERVENTION_UPDATE,
                                (row["assigned_to"], deadline, intervention[0]),
                            )
                        else:
                            cur.execute(
                                INTERVENTION_INSERT,
                                (
                                    alert_id,
                                    row["machine"],
                                    row["assigned_to"],
                                    deadline,
                                    datetime.now(timezone.utc).replace(tzinfo=None),
                                ),
                            )
                conn.commit()

        return row, None

    def get_dashboard_summary(self, current_user):
        """Get dashboard summary data (returns dicts with enriched user data due to joins)."""
        current_role = current_user.get("role")
        current_plant_id = current_user.get("plant_id")

        filters = []
        values = []
        if current_role != "superadmin":
            filters.append("a.plant_id = %s")
            values.append(current_plant_id)
        where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
        and_or_where = "AND" if where_clause else "WHERE"

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    DASHBOARD_COUNT_OPEN_ALERTS.format(
                        where_clause=where_clause, and_or_where=and_or_where
                    ),
                    tuple(values),
                )
                open_alerts = cur.fetchone()[0]

                cur.execute(
                    DASHBOARD_COUNT_PENDING_INTERVENTIONS.format(
                        where_clause=where_clause, and_or_where=and_or_where
                    ),
                    tuple(values),
                )
                pending_interventions = cur.fetchone()[0]

                cur.execute(
                    DASHBOARD_SELECT_RECENT_ALERTS.format(where_clause=where_clause),
                    tuple(values),
                )
                recent_alerts = rows_to_dicts(cur.fetchall())

                cur.execute(
                    DASHBOARD_SELECT_PENDING_LIST.format(
                        where_clause=where_clause, and_or_where=and_or_where
                    ),
                    tuple(values),
                )
                pending_list = rows_to_dicts(cur.fetchall())

        return {
            "active_machines": 4,
            "open_alerts": open_alerts,
            "pending_interventions": pending_interventions,
            "recent_alerts": recent_alerts,
            "pending_list": pending_list,
        }