from flask import Blueprint

from shared.auth import require_auth
from shared.http import get_json_body, json_error, json_response
from services.replay_service import ReplayService

iot_bp = Blueprint("iot", __name__)


@iot_bp.route("/status", methods=["GET"])
@require_auth()
def status():
    return json_response({"status": "ok", "service": "iot"})


@iot_bp.route("/inject", methods=["POST"])
@require_auth()
def inject():
    body = get_json_body()
    machine = body.get("machine")
    sensors = body.get("sensors")
    timestamp = body.get("timestamp")

    if machine not in ["moteur", "pompe", "compresseur", "echangeur"]:
        return json_error("Invalid machine.")
    if not isinstance(sensors, dict):
        return json_error("sensors must be an object.")

    payload = ReplayService().publish_machine_row(machine, {"timestamp": timestamp, **sensors})
    return json_response({"message": "Injected", "payload": payload}, 201)
