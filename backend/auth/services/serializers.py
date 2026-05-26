def serialize_user(user):
    """Serialize user row dict to API response format."""
    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "machines": user.get("machines") or [],
        "plant_id": user.get("plant_id"),
        "last_login": user.get("last_login"),
        "created_at": user.get("created_at"),
    }


def serialize_plant(plant):
    """Serialize plant row dict to API response format."""
    return {
        "id": plant.get("id"),
        "name": plant.get("name"),
        "code": plant.get("code"),
        "status": plant.get("status"),
        "contact_name": plant.get("contact_name"),
        "contact_email": plant.get("contact_email"),
        "contact_phone": plant.get("contact_phone"),
        "location": plant.get("location"),
        "industry": plant.get("industry"),
        "description": plant.get("description"),
        "approved_by": plant.get("approved_by"),
        "approved_at": plant.get("approved_at"),
        "created_at": plant.get("created_at"),
    }


def serialize_component(component):
    """Serialize component row dict to API response format."""
    return {
        "id": component.get("id"),
        "key": component.get("key"),
        "name": component.get("name"),
        "type": component.get("type"),
        "plant_id": component.get("plant_id"),
        "enabled": bool(component.get("enabled")),
        "created_at": component.get("created_at"),
        "updated_at": component.get("updated_at"),
    }
