from flask import Blueprint

from shared.auth import require_auth
from shared.http import get_json_body, json_error, json_response
from services.ml_service import MLService

finetune_bp = Blueprint("finetune", __name__)


@finetune_bp.route("", methods=["POST"])
@require_auth()
def finetune():
    body = get_json_body()
    machine = body.get("machine")
    model_name = body.get("model_name")

    if not machine:
        return json_error("machine is required.")
    if not model_name:
        return json_error("model_name is required.")

    response, status_code = MLService().finetune_model(machine, model_name)
    return json_response(response, status_code)


@finetune_bp.route("/status/<job_id>", methods=["GET"])
@require_auth()
def finetune_status(job_id):
    response, status_code = MLService().get_finetune_status(job_id)
    return json_response(response, status_code)
