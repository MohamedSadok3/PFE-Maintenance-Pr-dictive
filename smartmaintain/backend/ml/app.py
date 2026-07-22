import logging
import threading

from flask import Flask
from flask_cors import CORS

from shared.config import get_env
from shared.constants import ML_DEFAULT_PORT
from routes.predict import ml_bp
from routes.finetune import finetune_bp
from routes.status import status_bp
from routes.feedback import feedback_bp
from routes.reload import reload_bp
from services.ml_service import MLService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(ml_bp, url_prefix="/api/ml")
    app.register_blueprint(finetune_bp, url_prefix="/api/ml/finetune")
    app.register_blueprint(status_bp, url_prefix="/api/ml/status")
    app.register_blueprint(feedback_bp, url_prefix="/api/ml/feedback")
    app.register_blueprint(reload_bp, url_prefix="/api/ml")

    @app.route("/health", methods=["GET"])
    def health():
        ml_service = MLService()
        return {
            "status": "ok",
            "service": "ml",
            "mock_mode": ml_service.mock_ml,
        }

    return app


app = create_app()


def create_and_start_services():
    """Initialize services and start background threads."""
    ml_service = MLService()
    consumer_thread = threading.Thread(target=ml_service.consume_sensor_data, daemon=True)
    consumer_thread.start()
    return ml_service


# Start the Redis consumer when the module is loaded by any WSGI server
# (gunicorn, eventlet, etc.) — not just when run directly.
_ml_service = create_and_start_services()


if __name__ == "__main__":
    port = int(get_env("ML_PORT", str(ML_DEFAULT_PORT)))
    app.run(host="0.0.0.0", port=port, debug=False)
