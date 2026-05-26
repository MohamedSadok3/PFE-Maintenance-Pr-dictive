from flask import Blueprint, current_app, request

from shared.auth import get_current_user, require_auth
from shared.http import get_json_body, json_error, json_response
from services.alert_service import AlertService
from services.serializers import serialize_alert

alerts_bp = Blueprint("alerts", __name__)


@alerts_bp.route("", methods=["GET"])
@require_auth()
def list_alertes():
    current_user = get_current_user()
    filters = {
        "machine": request.args.get("machine"),
        "severity": request.args.get("severity"),
        "status": request.args.get("status"),
        "acknowledged": request.args.get("acknowledged"),
        "page": request.args.get("page", 1),
        "limit": request.args.get("limit", 20),
    }

    try:
        alerts, page, limit = AlertService().list_alerts(current_user, filters)
    except ValueError as e:
        return json_error(str(e))

    return json_response(
        {
            "alerts": [serialize_alert(alert) for alert in alerts],
            "page": page,
            "limit": limit,
        }
    )


@alerts_bp.route("/<int:alert_id>", methods=["GET"])
@require_auth()
def get_alerte(alert_id):
    current_user = get_current_user()
    alert = AlertService().get_alert_with_users(alert_id)
    if not alert:
        return json_error("Alert not found.", 404)

    if current_user.get("role") != "superadmin" and alert["plant_id"] != current_user.get("plant_id"):
        return json_error("Forbidden", 403)

    if current_user.get("role") == "technicien" and alert["assigned_to"] != int(current_user.get("sub")):
        return json_error("Forbidden", 403)

    return json_response({"alert": serialize_alert(alert)})


@alerts_bp.route("/<int:alert_id>", methods=["PATCH"])
@require_auth()
def patch_alerte(alert_id):
    current_user = get_current_user()
    data = get_json_body()

    alert_service = AlertService()
    alert, error = alert_service.update_alert(alert_id, data, current_user)
    if error:
        return json_error(error, 403 if "Forbidden" in error else 400)
    if not alert:
        return json_error("Alert not found.", 404)

    serialized = serialize_alert(alert)
    if hasattr(current_app, "socketio"):
        current_app.socketio.emit("alert:updated", serialized)

    return json_response({"alert": serialized})