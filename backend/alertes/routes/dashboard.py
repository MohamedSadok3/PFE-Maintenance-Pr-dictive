from flask import Blueprint

from shared.auth import get_current_user, require_auth
from shared.http import json_response
from services.alert_service import AlertService
from services.serializers import serialize_alert

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/summary", methods=["GET"])
@require_auth()
def dashboard_summary():
    current_user = get_current_user()
    summary_data = AlertService().get_dashboard_summary(current_user)

    summary_data["recent_alerts"] = [serialize_alert(alert) for alert in summary_data["recent_alerts"]]
    summary_data["pending_list"] = [serialize_alert(alert) for alert in summary_data["pending_list"]]

    return json_response(summary_data)