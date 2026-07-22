"""
Fine-tuning routes for SmartMaintain ML service.

POST /api/ml/finetune
    Body (multipart/form-data):
        machine    — machine type (moteur, pompe, compresseur, echangeur)
        model_name — name to give the new model version
        file       — CSV file with feature columns + a "label" column

    Body (application/json) — mock/test mode only:
        { "machine": "moteur", "model_name": "LSTM-moteur-v3" }
        Returns a synthetic job immediately (no real training).

GET /api/ml/finetune/status/<job_id>
    Returns the current state of a fine-tuning job.

GET /api/ml/finetune/jobs
    Lists all submitted fine-tuning jobs.
"""

from flask import Blueprint, request

from shared.auth import require_auth
from shared.constants import ROLE_ADMIN, ROLE_SUPERADMIN
from shared.http import get_json_body, json_error, json_response
from services.finetune_service import FineTuneService
from services.ml_service import MLService

finetune_bp = Blueprint("finetune", __name__)


@finetune_bp.route("", methods=["POST"])
@require_auth([ROLE_ADMIN, ROLE_SUPERADMIN])
def finetune():
    """
    Submit a fine-tuning job.

    Accepts either:
    - multipart/form-data with a CSV file (real training)
    - application/json without a file (mock mode — swaps active model name only)
    """
    ml_service = MLService()

    # ── Multipart upload (real training) ─────────────────────────────────
    if request.content_type and "multipart/form-data" in request.content_type:
        machine    = (request.form.get("machine") or "").strip().lower()
        model_name = (request.form.get("model_name") or "").strip()
        csv_file   = request.files.get("file")

        if not machine:
            return json_error("Le champ 'machine' est requis.")
        if not model_name:
            return json_error("Le champ 'model_name' est requis.")
        if not csv_file:
            return json_error("Un fichier CSV ('file') est requis pour l'entraînement réel.")

        csv_bytes = csv_file.read()
        service   = FineTuneService()
        response, status_code = service.submit_job(machine, model_name, csv_bytes)
        return json_response(response, status_code)

    # ── JSON body (mock / model-name-swap only) ───────────────────────────
    body       = get_json_body()
    machine    = (body.get("machine") or "").strip().lower()
    model_name = (body.get("model_name") or "").strip()

    if not machine:
        return json_error("Le champ 'machine' est requis.")
    if not model_name:
        return json_error("Le champ 'model_name' est requis.")

    response, status_code = ml_service.finetune_model(machine, model_name)
    return json_response(response, status_code)


@finetune_bp.route("/status/<job_id>", methods=["GET"])
@require_auth([ROLE_ADMIN, ROLE_SUPERADMIN])
def finetune_status(job_id):
    """Return the current status of a fine-tuning job."""
    response, status_code = FineTuneService().get_job_status(job_id)
    return json_response(response, status_code)


@finetune_bp.route("/jobs", methods=["GET"])
@require_auth([ROLE_ADMIN, ROLE_SUPERADMIN])
def list_jobs():
    """List all fine-tuning jobs submitted in this session."""
    response, status_code = FineTuneService().list_jobs()
    return json_response(response, status_code)
