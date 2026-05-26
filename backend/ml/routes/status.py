from flask import Blueprint

from shared.auth import require_auth
from shared.http import json_response
from services.ml_service import MLService

status_bp = Blueprint("status", __name__)


@status_bp.route("", methods=["GET"])
@require_auth()
def status():
    response = MLService().get_status()
    return json_response(response)