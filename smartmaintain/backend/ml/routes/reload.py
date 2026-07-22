"""
API endpoint for hot-reloading ML models.

Allows deploying newly trained models from Colab without restarting the service.
"""
from flask import Blueprint, request

from shared.auth import require_auth
from shared.http import json_error, json_response
from services.ml_service import MLService

reload_bp = Blueprint("reload", __name__)


@reload_bp.route("/reload", methods=["POST"])
@require_auth(require_role=["admin"])
def reload_models():
    """
    Hot-reload ML models without restarting the service.
    
    This endpoint is called after uploading new model files (.pkl)
    to deploy them immediately without downtime.
    
    Query params:
        - machine: Specific machine to reload (optional, default: all)
    
    Example:
        POST /api/ml/reload?machine=pompe
        POST /api/ml/reload  (reloads all)
    """
    machine = request.args.get("machine")
    
    if machine and machine not in ["moteur", "pompe", "compresseur", "echangeur"]:
        return json_error(f"Invalid machine type: {machine}")
    
    service = MLService()
    result = service.reload_models(machine=machine)
    
    if result.get("success"):
        return json_response(result, 200)
    else:
        return json_error(result.get("message", "Model reload failed"), 500)


@reload_bp.route("/reload/verify", methods=["GET"])
@require_auth(require_role=["admin"])
def verify_models():
    """
    Verify which models are currently loaded.
    
    Useful for checking if new models are active after reload.
    """
    service = MLService()
    
    loaded_models = {}
    if hasattr(service.engine, 'models'):
        for machine in service.engine.models.keys():
            metadata = service.engine.metadata.get(machine, {})
            loaded_models[machine] = {
                "model_name": service.active_models.get(machine),
                "accuracy": metadata.get("accuracy"),
                "classes": metadata.get("classes"),
                "n_features": metadata.get("n_features"),
            }
    
    return json_response({
        "mock_mode": service.mock_ml,
        "loaded_models": loaded_models,
        "count": len(loaded_models),
    })
