import json
from typing import List, Optional

from shared.entity import isoformat_value, mapping_from_row


class User:
    """Utilisateur de la plateforme."""

    def __init__(
        self,
        id,
        name,
        email,
        role,
        plant_id=None,
        machines=None,
        last_login=None,
        created_at=None,
        password_hash=None,
    ):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.plant_id = plant_id
        self.machines = machines or []
        self.last_login = last_login
        self.created_at = created_at
        self.password_hash = password_hash

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "plant_id": self.plant_id,
            "machines": self.machines or [],
            "last_login": isoformat_value(self.last_login),
            "created_at": isoformat_value(self.created_at),
        }

    @staticmethod
    def from_row(row) -> Optional["User"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return User(
            id=data.get("id"),
            name=data.get("name"),
            email=data.get("email"),
            role=data.get("role"),
            plant_id=data.get("plant_id"),
            machines=data.get("machines") or [],
            last_login=data.get("last_login"),
            created_at=data.get("created_at"),
            password_hash=data.get("password_hash"),
        )

    @classmethod
    def from_rows(cls, rows) -> List["User"]:
        return [user for row in rows if (user := cls.from_row(row))]


class Plant:
    """Usine cliente."""

    def __init__(
        self,
        id,
        name,
        code,
        status,
        contact_name=None,
        contact_email=None,
        contact_phone=None,
        location=None,
        industry=None,
        description=None,
        approved_by=None,
        approved_at=None,
        created_at=None,
    ):
        self.id = id
        self.name = name
        self.code = code
        self.status = status
        self.contact_name = contact_name
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.location = location
        self.industry = industry
        self.description = description
        self.approved_by = approved_by
        self.approved_at = approved_at
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "status": self.status,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "location": self.location,
            "industry": self.industry,
            "description": self.description,
            "approved_by": self.approved_by,
            "approved_at": isoformat_value(self.approved_at),
            "created_at": isoformat_value(self.created_at),
        }

    @staticmethod
    def from_row(row) -> Optional["Plant"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return Plant(
            id=data.get("id"),
            name=data.get("name"),
            code=data.get("code"),
            status=data.get("status"),
            contact_name=data.get("contact_name"),
            contact_email=data.get("contact_email"),
            contact_phone=data.get("contact_phone"),
            location=data.get("location"),
            industry=data.get("industry"),
            description=data.get("description"),
            approved_by=data.get("approved_by"),
            approved_at=data.get("approved_at"),
            created_at=data.get("created_at"),
        )

    @classmethod
    def from_rows(cls, rows) -> List["Plant"]:
        return [plant for row in rows if (plant := cls.from_row(row))]


class Component:
    """Composant / machine surveillée dans une usine."""

    def __init__(
        self,
        id,
        key,
        name,
        type,
        plant_id,
        enabled=True,
        created_at=None,
        updated_at=None,
    ):
        self.id = id
        self.key = key
        self.name = name
        self.type = type
        self.plant_id = plant_id
        self.enabled = enabled
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "type": self.type,
            "plant_id": self.plant_id,
            "enabled": bool(self.enabled),
            "created_at": isoformat_value(self.created_at),
            "updated_at": isoformat_value(self.updated_at),
        }

    @staticmethod
    def from_row(row) -> Optional["Component"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return Component(
            id=data.get("id"),
            key=data.get("key"),
            name=data.get("name"),
            type=data.get("type"),
            plant_id=data.get("plant_id"),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def from_rows(cls, rows) -> List["Component"]:
        return [component for row in rows if (component := cls.from_row(row))]


class PlantRegistration:
    """Demande d'inscription d'une usine."""

    def __init__(
        self,
        id,
        plant_name,
        plant_code,
        contact_name,
        contact_email,
        payload,
        status,
        review_note=None,
        reviewed_by=None,
        reviewed_at=None,
        created_at=None,
    ):
        self.id = id
        self.plant_name = plant_name
        self.plant_code = plant_code
        self.contact_name = contact_name
        self.contact_email = contact_email
        self.payload = payload
        self.status = status
        self.review_note = review_note
        self.reviewed_by = reviewed_by
        self.reviewed_at = reviewed_at
        self.created_at = created_at

    @property
    def payload_data(self) -> dict:
        if isinstance(self.payload, dict):
            return self.payload
        if isinstance(self.payload, str):
            return json.loads(self.payload)
        return {}

    def to_dict(self) -> dict:
        payload = self.payload
        if isinstance(payload, dict):
            payload = json.dumps(payload)
        payload_data = self.payload_data
        return {
            "id": self.id,
            "plant_name": self.plant_name,
            "plant_code": self.plant_code,
            "contact_name": self.contact_name,
            "contact_email": self.contact_email,
            "payload": payload,
            "payload_data": payload_data,
            "documents": payload_data.get("documents") or {},
            "status": self.status,
            "review_note": self.review_note,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": isoformat_value(self.reviewed_at),
            "created_at": isoformat_value(self.created_at),
        }

    @staticmethod
    def from_row(row) -> Optional["PlantRegistration"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return PlantRegistration(
            id=data.get("id"),
            plant_name=data.get("plant_name"),
            plant_code=data.get("plant_code"),
            contact_name=data.get("contact_name"),
            contact_email=data.get("contact_email"),
            payload=data.get("payload"),
            status=data.get("status"),
            review_note=data.get("review_note"),
            reviewed_by=data.get("reviewed_by"),
            reviewed_at=data.get("reviewed_at"),
            created_at=data.get("created_at"),
        )

    @classmethod
    def from_rows(cls, rows) -> List["PlantRegistration"]:
        return [item for row in rows if (item := cls.from_row(row))]
