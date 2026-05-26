import re
import json
import bcrypt
from psycopg2 import errors

from shared.database import get_db_connection
from shared.rows import row_to_dict, rows_to_dicts
from .email_service import EmailService
from queries import (
    REGISTRATION_CHECK_PLANT_EXISTS,
    REGISTRATION_CHECK_PENDING_EXISTS,
    REGISTRATION_CHECK_EMAILS_TAKEN,
    REGISTRATION_INSERT,
    REGISTRATION_SELECT_ALL,
    REGISTRATION_SELECT_BY_STATUS,
    REGISTRATION_SELECT_BY_ID,
    REGISTRATION_REJECT,
    REGISTRATION_INSERT_USER,
    REGISTRATION_APPROVE,
    PLANT_INSERT_ON_APPROVE,
)

PLANT_CODE_PATTERN = re.compile(r"^[a-z0-9-]{3,32}$")


def _registration_payload(registration):
    payload = registration.get("payload") or {}
    if isinstance(payload, str):
        return json.loads(payload)
    return payload


class RegistrationService:
    def __init__(self):
        self.email_service = EmailService()

    def register_plant(self, plant_data, users_data, documents=None):
        """Register a new plant with initial users and optional legal documents."""
        plant_name = (plant_data.get("name") or "").strip()
        plant_code = (plant_data.get("code") or "").strip().lower()
        contact_name = (plant_data.get("contact_name") or "").strip()
        contact_email = (plant_data.get("contact_email") or "").strip().lower()

        if not all([plant_name, plant_code, contact_name, contact_email]):
            return None, "Les informations de l'usine sont incomplètes."
        if not PLANT_CODE_PATTERN.match(plant_code):
            return None, "Le code usine doit contenir uniquement [a-z0-9-] et faire entre 3 et 32 caractères."

        admin_user = users_data.get("admin") or {}
        if not all((admin_user.get(field) or "").strip() for field in ("name", "email", "password")):
            return None, "Le compte administrateur est requis (nom, email, mot de passe)."

        if not documents or not documents.get("patente") or not documents.get("rne"):
            return None, "Les documents Patente et RNE sont obligatoires."

        patente_doc = documents.get("patente") or {}
        rne_doc = documents.get("rne") or {}
        if not patente_doc.get("data"):
            return None, "Le document Patente est manquant ou invalide."
        if not rne_doc.get("data"):
            return None, "Le document RNE est manquant ou invalide."

        emails = [admin_user.get("email", "").strip().lower(), contact_email]
        if len(set(emails)) != len(emails):
            return None, "Les adresses email doivent être distinctes dans la demande d'inscription."

        payload = {
            "plant": {
                "name": plant_name,
                "code": plant_code,
                "contact_name": contact_name,
                "contact_email": contact_email,
            },
            "users": {
                "admin": {
                    "name": admin_user.get("name", "").strip(),
                    "email": admin_user.get("email", "").strip().lower(),
                    "password": admin_user.get("password", ""),
                    "machines": [],
                },
            },
            "documents": {
                "patente": {"data": patente_doc.get("data"), "name": patente_doc.get("name", "patente.pdf")},
                "rne": {"data": rne_doc.get("data"), "name": rne_doc.get("name", "rne.pdf")},
            },
        }

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(REGISTRATION_CHECK_PLANT_EXISTS, (plant_code, plant_name))
                if cur.fetchone():
                    return None, "Cette usine existe déjà."
                cur.execute(REGISTRATION_CHECK_PENDING_EXISTS, (plant_code, plant_name))
                if cur.fetchone():
                    return None, "Une demande d'inscription est déjà en attente pour cette usine."
                cur.execute(REGISTRATION_CHECK_EMAILS_TAKEN, (emails,))
                if cur.fetchone():
                    return None, "Un ou plusieurs emails sont déjà utilisés."

                cur.execute(
                    REGISTRATION_INSERT,
                    (plant_name, plant_code, contact_name, contact_email, json.dumps(payload)),
                )
                row = cur.fetchone()
                registration = row_to_dict(row)
                conn.commit()

        return registration, None

    def list_registrations(self, status="pending"):
        """List plant registrations."""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if status == "all":
                    cur.execute(REGISTRATION_SELECT_ALL)
                else:
                    cur.execute(REGISTRATION_SELECT_BY_STATUS, (status,))
                rows = cur.fetchall()
                return rows_to_dicts(rows)

    def review_registration(self, registration_id, action, review_note, reviewer_id):
        """Approve or reject a plant registration."""
        if action not in {"approve", "reject"}:
            return None, "L'action doit être 'approve' ou 'reject'."

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(REGISTRATION_SELECT_BY_ID, (registration_id,))
                row = cur.fetchone()
                registration = row_to_dict(row)
                if not registration:
                    return None, "Inscription introuvable."
                if registration["status"] != "pending":
                    return None, "Cette inscription a déjà été traitée."

                if action == "reject":
                    cur.execute(REGISTRATION_REJECT, (review_note, reviewer_id, registration_id))
                    row = cur.fetchone()
                    reviewed = row_to_dict(row)
                    conn.commit()
                    return reviewed, None

                payload = _registration_payload(registration)
                plant_payload = payload.get("plant") or {}
                users_payload = payload.get("users") or {}
                admin_payload = users_payload.get("admin") or {}

                cur.execute(
                    PLANT_INSERT_ON_APPROVE,
                    (
                        plant_payload.get("name"),
                        plant_payload.get("code"),
                        plant_payload.get("contact_name"),
                        plant_payload.get("contact_email"),
                        reviewer_id,
                    ),
                )
                plant_row = cur.fetchone()
                plant = row_to_dict(plant_row)

                for role_key in ("admin", "superviseur", "technicien"):
                    user_payload = users_payload.get(role_key)
                    if not user_payload:
                        continue
                    password_hash = bcrypt.hashpw(
                        user_payload.get("password", "").encode("utf-8"),
                        bcrypt.gensalt(),
                    ).decode("utf-8")
                    cur.execute(
                        REGISTRATION_INSERT_USER,
                        (
                            user_payload.get("name"),
                            user_payload.get("email"),
                            password_hash,
                            role_key,
                            plant["id"],
                            user_payload.get("machines") or [],
                        ),
                    )

                cur.execute(REGISTRATION_APPROVE, (review_note, reviewer_id, registration_id))
                row = cur.fetchone()
                reviewed = row_to_dict(row)
                conn.commit()

        recipients = []
        contact_email = plant_payload.get("contact_email")
        if contact_email:
            recipients.append(
                (
                    contact_email,
                    plant_payload.get("contact_name") or "Responsable usine",
                )
            )
        admin_email = admin_payload.get("email")
        if admin_email and admin_email != contact_email:
            recipients.append((admin_email, admin_payload.get("name") or "Admin usine"))

        for recipient_email, recipient_name in recipients:
            self.email_service.send_registration_approved_email(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                plant_name=plant_payload.get("name") or registration["plant_name"],
                plant_code=plant_payload.get("code") or registration["plant_code"],
            )

        return reviewed, plant
