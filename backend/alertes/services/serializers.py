from datetime import date, datetime


def _iso(value):
    if not value:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def serialize_alert(alert):
    """Serialize alert row dict for API responses."""
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
        "created_at": _iso(alert.get("created_at")),
        "resolved_at": _iso(alert.get("resolved_at")),
        "validation_at": _iso(alert.get("resolved_at")),
    }
