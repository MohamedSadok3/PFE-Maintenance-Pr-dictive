import threading

from flask import Flask
from flask_cors import CORS

from shared.config import get_env
from shared.constants import ML_DEFAULT_PORT
from routes.predict import ml_bp
from routes.finetune import finetune_bp
from routes.status import status_bp
from services.ml_service import MLService

app = Flask(__name__)
CORS(app)


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)

    # Register blueprints
    app.register_blueprint(ml_bp, url_prefix='/api/ml')
    app.register_blueprint(finetune_bp, url_prefix='/api/ml/finetune')
    app.register_blueprint(status_bp, url_prefix='/api/ml/status')

    return app


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    ml_service = MLService()
    return {
        "status": "ok",
        "service": "ml",
        "mock_mode": ml_service.mock_ml
    }


def create_and_start_services(app):
    """Initialize services and start background threads."""
    ml_service = MLService()

    # Start Redis consumer thread
    consumer_thread = threading.Thread(target=ml_service.consume_sensor_data, daemon=True)
    consumer_thread.start()

    return ml_service


if __name__ == "__main__":
    app = create_app()
    create_and_start_services(app)
    port = int(get_env("ML_PORT", str(ML_DEFAULT_PORT)))
    app.run(host="0.0.0.0", port=port, debug=False)
