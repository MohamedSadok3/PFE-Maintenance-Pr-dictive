import requests

from shared.config import get_env


class EmailService:
    def __init__(self):
        self.api_key = get_env("RESEND_API_KEY")
        self.from_email = get_env("RESEND_FROM_EMAIL")
        self.api_url = get_env("RESEND_API_URL", "https://api.resend.com/emails")
        self.app_base_url = get_env("APP_BASE_URL", "http://localhost:3000")

    def send_registration_approved_email(self, recipient_email, recipient_name, plant_name, plant_code):
        """Send email notification when plant registration is approved."""
        if not self.api_key or not self.from_email:
            print("Skipping approval email: Resend is not configured.")
            return False
        if not recipient_email:
            return False

        login_url = f"{self.app_base_url.rstrip('/')}/login"
        subject = f"Inscription de l'usine {plant_name} approuvee"
        body = (
            f"Bonjour {recipient_name or ''},\n\n"
            f"L'inscription de votre usine a ete approuvee.\n\n"
            f"Nom de l'usine: {plant_name}\n"
            f"Code usine: {plant_code}\n\n"
            f"Vous pouvez vous connecter ici: {login_url}\n\n"
            "Cordialement,\n"
            "Equipe SmartMaintain"
        )

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": self.from_email,
                    "to": [recipient_email],
                    "subject": subject,
                    "text": body,
                },
                timeout=10,
            )
            response.raise_for_status()
            return True
        except Exception as exc:
            print(f"Failed to send approval email to {recipient_email}: {exc}")
            return False