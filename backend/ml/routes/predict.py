from flask import Blueprint

from shared.auth import require_auth
from shared.http import get_json_body, json_error, json_response
from services.ml_service import MLService

ml_bp = Blueprint("ml", __name__)


@ml_bp.route("/predict", methods=["POST"])
@require_auth()
def predict():
    body = get_json_body()
    machine = body.get("machine")
    sensors = body.get("sensors")

    if not machine or not isinstance(sensors, dict):
        return json_error("machine and sensors are required.")

    response, status_code = MLService().predict_for_machine(machine, sensors)
    return json_response(response, status_code)
