import eventlet
eventlet.monkey_patch()

import os
import threading
import jwt
import requests
import socketio
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
load_dotenv()

PORT = 5000
JWT_SECRET = os.environ.get("JWT_SECRET", "supersecretkey123")
AUTH_URL = os.environ.get("AUTH_URL", "http://auth:5004")
IOT_URL = os.environ.get("IOT_URL", "http://iot:5001")
ML_URL = os.environ.get("ML_URL", "http://ml:5002")
ALERTES_URL = os.environ.get("ALERTES_URL", "http://alertes:5003")
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("FRONTEND_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    if origin.strip()
]

SERVICE_MAP = {
    "auth": AUTH_URL,
    "users": AUTH_URL,
    "plants": AUTH_URL,
    "components": AUTH_URL,
    "iot": IOT_URL,
    "ml": ML_URL,
    "alertes": ALERTES_URL,
    "dashboard": ALERTES_URL,
}

app = Flask(__name__)
CORS(app, origins=FRONTEND_ORIGINS, supports_credentials=True)
socketio_server = SocketIO(
    app, cors_allowed_origins=FRONTEND_ORIGINS, async_mode="eventlet"
)

alertes_socket = socketio.Client(reconnection=True)


def _build_target_url(section, path):
    base = SERVICE_MAP[section]
    if path:
        return f"{base}/api/{section}/{path}"
    return f"{base}/api/{section}"


def _proxy_request(section, path=""):
    target_url = _build_target_url(section, path)

    excluded_headers = {"host", "content-length"}
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in excluded_headers
    }

    upstream_response = requests.request(
        method=request.method,
        url=target_url,
        headers=headers,
        params=request.args,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        timeout=15,
    )

    response_headers = [
        (name, value)
        for name, value in upstream_response.headers.items()
        if name.lower() not in {"content-encoding", "transfer-encoding", "connection"}
    ]

    return Response(
        response=upstream_response.content,
        status=upstream_response.status_code,
        headers=response_headers,
    )


def _is_public_route():
    if request.path == "/health" and request.method == "GET":
        return True
    if request.path == "/api/auth/login" and request.method == "POST":
        return True
    if request.path == "/api/auth/register-plant" and request.method == "POST":
        return True
    return False


@app.before_request
def require_jwt():
    if request.method == "OPTIONS":
        return None
    if _is_public_route():
        return None
    if not request.path.startswith("/api/"):
        return None

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Unauthorized"}), 401

    token = auth_header.split(" ", 1)[1].strip()
    try:
        jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return jsonify({"error": "Unauthorized"}), 401
    return None


@app.route("/api/auth", defaults={"path": ""}, methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
@app.route("/api/auth/<path:path>", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def proxy_auth(path):
    return _proxy_request("auth", path)


@app.route("/api/users", defaults={"path": ""}, methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
@app.route("/api/users/<path:path>", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def proxy_users(path):
    return _proxy_request("users", path)


@app.route("/api/components", defaults={"path": ""}, methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
@app.route("/api/components/<path:path>", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def proxy_components(path):
    return _proxy_request("components", path)


@app.route("/api/plants", defaults={"path": ""}, methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
@app.route("/api/plants/<path:path>", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def proxy_plants(path):
    return _proxy_request("plants", path)


@app.route("/api/iot", defaults={"path": ""}, methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
@app.route("/api/iot/<path:path>", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def proxy_iot(path):
    return _proxy_request("iot", path)


@app.route("/api/ml", defaults={"path": ""}, methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
@app.route("/api/ml/<path:path>", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def proxy_ml(path):
    return _proxy_request("ml", path)


@app.route("/api/alertes", defaults={"path": ""}, methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
@app.route("/api/alertes/<path:path>", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def proxy_alertes(path):
    return _proxy_request("alertes", path)


@app.route(
    "/api/dashboard", defaults={"path": ""}, methods=["GET", "POST", "PATCH", "PUT", "DELETE"]
)
@app.route("/api/dashboard/<path:path>", methods=["GET", "POST", "PATCH", "PUT", "DELETE"])
def proxy_dashboard(path):
    return _proxy_request("dashboard", path)


@app.route("/health", methods=["GET"])
def health():
    services = {
        "auth": AUTH_URL,
        "iot": IOT_URL,
        "ml": ML_URL,
        "alertes": ALERTES_URL,
    }
    health_status = {"gateway": "ok"}

    for name, base_url in services.items():
        try:
            response = requests.get(f"{base_url}/health", timeout=3)
            is_ok = response.status_code == 200 and response.json().get("status") == "ok"
            health_status[name] = "ok" if is_ok else "error"
        except Exception:
            health_status[name] = "error"

    return jsonify(health_status)


@alertes_socket.on("alert:new")
def on_alert_new(data):
    socketio_server.emit("alert:new", data)


@alertes_socket.on("alert:updated")
def on_alert_updated(data):
    socketio_server.emit("alert:updated", data)


@alertes_socket.on("sensor:data")
def on_sensor_data(data):
    socketio_server.emit("sensor:data", data)


def connect_to_alertes():
    try:
        alertes_socket.connect(ALERTES_URL, transports=["websocket", "polling"])
        alertes_socket.wait()
    except Exception:
        # Keep gateway alive even if alertes socket is temporarily unavailable.
        pass


bridge_thread = threading.Thread(target=connect_to_alertes, daemon=True)
bridge_thread.start()

if __name__ == "__main__":
    socketio_server.run(app, host="0.0.0.0", port=PORT, debug=False)
