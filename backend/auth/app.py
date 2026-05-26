from flask import Flask
from flask_cors import CORS

from shared.config import get_env
from routes.auth import auth_bp
from routes.users import users_bp
from routes.plants import plants_bp
from routes.components import components_bp


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(plants_bp, url_prefix='/api/plants')
    app.register_blueprint(components_bp, url_prefix='/api/components')

    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok", "service": "auth"}

    return app


app = create_app()


# Initialize database on startup
from services.registration_service import RegistrationService
_registration_service = RegistrationService()  # This will initialize the database


if __name__ == "__main__":
    port = int(get_env("AUTH_PORT", "5004"))
    app.run(host="0.0.0.0", port=port, debug=False)