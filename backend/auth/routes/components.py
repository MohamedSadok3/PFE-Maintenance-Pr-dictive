from flask import Blueprint, jsonify, request

from shared.auth import require_auth
from services.component_service import ComponentService
from services.serializers import serialize_component

components_bp = Blueprint("components", __name__)


def get_current_user():
    user = getattr(request, "current_user", {}) or {}
    return user.get("role"), user.get("plant_id")


def json_error(message, status=400):
    return jsonify({"error": message}), status


@components_bp.route("", methods=["GET"])
@require_auth(["superadmin", "admin", "superviseur", "technicien"])
def list_components():
    current_role, current_plant_id = get_current_user()
    plant_id = request.args.get("plant_id")
    components = ComponentService.list_components(current_role, current_plant_id, plant_id)
    return jsonify({"components": [serialize_component(component) for component in components]})


@components_bp.route("", methods=["POST"])
@require_auth(["superadmin", "admin"])
def create_component():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    component_type = (data.get("type") or "").strip().lower()
    if not name or not component_type:
        return json_error("name and type are required.")

    enabled = bool(data.get("enabled", True))
    current_role, current_plant_id = get_current_user()
    component, error = ComponentService.create_component(
        name,
        component_type,
        enabled,
        current_role,
        current_plant_id,
        data.get("plant_id"),
    )

    if error:
        status = 409 if "already exists" in error else 400
        return json_error(error, status)

    return jsonify({"component": serialize_component(component)}), 201


@components_bp.route("/<int:component_id>", methods=["PATCH"])
@require_auth(["superadmin", "admin"])
def update_component(component_id):
    data = request.get_json(silent=True) or {}
    current_role, current_plant_id = get_current_user()
    component, error = ComponentService.update_component(component_id, data, current_role, current_plant_id)

    if error:
        status = 409 if "already exists" in error else 400
        return json_error(error, status)

    return jsonify({"component": serialize_component(component)})


@components_bp.route("/<int:component_id>", methods=["DELETE"])
@require_auth(["superadmin", "admin"])
def delete_component(component_id):
    current_role, current_plant_id = get_current_user()
    if ComponentService.delete_component(component_id, current_role, current_plant_id):
        return jsonify({"message": "Component deleted successfully."})
    return json_error("Component not found.", 404)
