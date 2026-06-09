import eventlet
eventlet.monkey_patch()

import threading
import requests
import socketio
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO

from shared.config import get_env
from shared.constants import (
    ALERTES_SERVICE_DEFAULT_URL,
    AUTH_SERVICE_DEFAULT_URL,
    FRONTEND_DEFAULT_ORIGINS,
    GATEWAY_DEFAULT_PORT,
    IOT_SERVICE_DEFAULT_URL,
    ML_SERVICE_DEFAULT_URL,
)
from shared.auth import decode_token

PORT = int(get_env("GATEWAY_PORT", str(GATEWAY_DEFAULT_PORT)))
AUTH_URL = get_env("AUTH_URL", AUTH_SERVICE_DEFAULT_URL)
IOT_URL = get_env("IOT_URL", IOT_SERVICE_DEFAULT_URL)
ML_URL = get_env("ML_URL", ML_SERVICE_DEFAULT_URL)
ALERTES_URL = get_env("ALERTES_URL", ALERTES_SERVICE_DEFAULT_URL)
FRONTEND_ORIGINS = [
    origin.strip()
    for origin in get_env("FRONTEND_ORIGINS", ",".join(FRONTEND_DEFAULT_ORIGINS)).split(",")
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
        decode_token(token)
    except Exception:
        return jsonify({"error": "Unauthorized"}), 401
    return None


PROXY_SECTIONS = [
    "auth",
    "users",
    "components",
    "plants",
    "iot",
    "ml",
    "alertes",
    "dashboard",
]

for section in PROXY_SECTIONS:
    endpoint = f"proxy_{section}"
    app.add_url_rule(
        f"/api/{section}",
        endpoint,
        (lambda section: (lambda path="": _proxy_request(section, path)))(section),
        methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    )
    app.add_url_rule(
        f"/api/{section}/<path:path>",
        f"{endpoint}_path",
        (lambda section: (lambda path: _proxy_request(section, path)))(section),
        methods=["GET", "POST", "PATCH", "PUT", "DELETE"],
    )


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
