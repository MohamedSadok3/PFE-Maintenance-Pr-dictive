from flask import Blueprint

from shared.auth import get_current_user, require_auth
from shared.constants import MACHINE_TYPES, ROLE_ADMIN
from shared.http import get_json_body, json_error, json_response
from services.config_service import ConfigService
from services.replay_service import ReplayService

iot_bp = Blueprint("iot", __name__)
config_service = ConfigService()


@iot_bp.route("/status", methods=["GET"])
@require_auth()
def status():
    return json_response({"status": "ok", "service": "iot"})


@iot_bp.route("/config", methods=["GET"])
@require_auth([ROLE_ADMIN])
def get_config():
    current_user = get_current_user()
    plant_id = current_user.get("plant_id")
    if not plant_id:
        return json_error("Aucune usine associée à cet administrateur.", 403)

    mqtt, sensors = config_service.get_config(int(plant_id))
    return json_response(
        {
            "mqtt": mqtt.to_dict() if mqtt else None,
            "sensors": [item.to_dict() for item in sensors],
        }
    )


@iot_bp.route("/config", methods=["POST"])
@require_auth([ROLE_ADMIN])
def save_config():
    current_user = get_current_user()
    plant_id = current_user.get("plant_id")
    if not plant_id:
        return json_error("Aucune usine associée à cet administrateur.", 403)

    body = get_json_body()
    mqtt_payload = body.get("mqtt")
    sensors_payload = body.get("sensors")

    if not mqtt_payload and not sensors_payload:
        return json_error("Aucune donnée de configuration fournie.")

    mqtt, sensors = config_service.save_config(
        int(plant_id),
        mqtt_payload=mqtt_payload,
        sensors_payload=sensors_payload,
    )
    return json_response(
        {
            "mqtt": mqtt.to_dict() if mqtt else None,
            "sensors": [item.to_dict() for item in sensors],
        }
    )


@iot_bp.route("/config/test", methods=["POST"])
@require_auth([ROLE_ADMIN])
def test_mqtt_config():
    body = get_json_body()
    host = body.get("host")
    port = body.get("port", 1883)
    username = body.get("username")
    password = body.get("password")

    ok, message = config_service.test_mqtt_connection(host, port, username, password)
    if not ok:
        return json_error(message, 400)
    return json_response({"message": message})


@iot_bp.route("/inject", methods=["POST"])
@require_auth()
def inject():
    body = get_json_body()
    machine = body.get("machine")
    sensors = body.get("sensors")
    timestamp = body.get("timestamp")

    if machine not in MACHINE_TYPES:
        return json_error("Invalid machine.")
    if not isinstance(sensors, dict):
        return json_error("sensors must be an object.")

    payload = ReplayService().publish_machine_row(machine, {"timestamp": timestamp, **sensors})
    return json_response({"message": "Injected", "payload": payload}, 201)
