import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

from shared.config import get_env
from routes.alerts import alerts_bp
from routes.dashboard import dashboard_bp
from services.alert_service import AlertService
from services.redis_consumer import RedisConsumer


def create_app():
    """Create and configure the Flask application with SocketIO."""
    app = Flask(__name__)
    CORS(app)

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

    # Register blueprints
    app.register_blueprint(alerts_bp, url_prefix='/api/alertes')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')

    # Store socketio instance on app for access in routes
    app.socketio = socketio

    @app.route("/health", methods=["GET"])
    def health():
        return {"status": "ok", "service": "alertes"}

    return app, socketio


app, socketio = create_app()


def create_and_start_services(app, socketio):
    """Initialize services and start background threads."""
    # Initialize database
    alert_service = AlertService()
    alert_service.init_db()

    # Start Redis consumer
    redis_consumer = RedisConsumer(socketio)
    redis_consumer.start_consumer_thread()

    return alert_service, redis_consumer


if __name__ == "__main__":
    app, socketio = create_app()
    alert_service, redis_consumer = create_and_start_services(app, socketio)

    port = int(get_env("ALERTES_PORT", "5003"))
    socketio.run(app, host="0.0.0.0", port=port, debug=False)