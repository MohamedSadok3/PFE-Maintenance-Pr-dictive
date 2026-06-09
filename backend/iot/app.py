import threading
from flask import Flask, jsonify
from flask_cors import CORS

from shared.config import get_env
from shared.constants import IOT_DEFAULT_PORT
from routes.iot import iot_bp
from services.config_service import ConfigService
from services.replay_service import ReplayService

app = Flask(__name__)
CORS(app)
app.register_blueprint(iot_bp, url_prefix='/api/iot')


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(iot_bp, url_prefix='/api/iot')

    return app


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "iot"})


def create_and_start_services(app):
    """Initialize services and start background threads."""
    ConfigService().init_db()
    replay_service = ReplayService()
    replay_service.start_replay_threads()
    return replay_service


if __name__ == "__main__":
    app = create_app()
    create_and_start_services(app)
    port = int(get_env("IOT_PORT", str(IOT_DEFAULT_PORT)))
    app.run(host="0.0.0.0", port=port, debug=False)
