import json
import os
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import redis
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
PORT = 5001
CHANNEL_NAME = "sensor_data"
DATA_DIR = Path(__file__).parent / "data"
ROWS_PER_FILE = 500
REPLAY_INTERVAL_SECONDS = 2

app = Flask(__name__)
CORS(app)

state_lock = threading.Lock()
service_state = {
    "mode": "csv_replay",
    "last_received": {
        "moteur": None,
        "pompe": None,
        "compresseur": None,
        "echangeur": None,
    },
}

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def _build_timestamps():
    start = datetime(2025, 1, 1, 0, 0, 0)
    return [(start + timedelta(minutes=i)).isoformat() for i in range(ROWS_PER_FILE)]


def _insert_spikes(values, ratio, low_factor=1.6, high_factor=2.4):
    values = np.array(values, copy=True)
    count = max(1, int(len(values) * ratio))
    spike_indexes = np.random.choice(len(values), count, replace=False)
    scale = np.random.uniform(low_factor, high_factor, size=count)
    values[spike_indexes] *= scale
    return values


def generate_csv_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamps = _build_timestamps()

    moteur = pd.DataFrame(
        {
            "timestamp": timestamps,
            "vibration": np.random.normal(0.35, 0.05, ROWS_PER_FILE),
            "current": np.random.normal(11.8, 1.1, ROWS_PER_FILE),
            "temperature": np.random.normal(72.0, 3.2, ROWS_PER_FILE),
        }
    )
    moteur["vibration"] = _insert_spikes(moteur["vibration"].to_numpy(), 0.10, 2.0, 3.2)
    moteur["current"] = _insert_spikes(moteur["current"].to_numpy(), 0.10, 1.4, 2.0)
    moteur["temperature"] = _insert_spikes(moteur["temperature"].to_numpy(), 0.10, 1.2, 1.5)

    pompe = pd.DataFrame(
        {
            "timestamp": timestamps,
            "pressure_in": np.random.normal(4.8, 0.4, ROWS_PER_FILE),
            "pressure_out": np.random.normal(8.6, 0.5, ROWS_PER_FILE),
            "flow_rate": np.random.normal(128.0, 8.0, ROWS_PER_FILE),
            "vibration": np.random.normal(0.24, 0.03, ROWS_PER_FILE),
        }
    )
    pompe["flow_rate"] = _insert_spikes(pompe["flow_rate"].to_numpy(), 0.06, 0.65, 0.85)
    pompe["vibration"] = _insert_spikes(pompe["vibration"].to_numpy(), 0.07, 1.8, 2.7)

    compresseur = pd.DataFrame(
        {
            "timestamp": timestamps,
            "pressure": np.random.normal(10.5, 0.6, ROWS_PER_FILE),
            "temperature_oil": np.random.normal(83.0, 3.0, ROWS_PER_FILE),
            "temperature_air": np.random.normal(41.0, 2.0, ROWS_PER_FILE),
            "current": np.random.normal(18.2, 1.4, ROWS_PER_FILE),
        }
    )
    compresseur["pressure"] = _insert_spikes(compresseur["pressure"].to_numpy(), 0.08, 1.3, 1.8)
    compresseur["current"] = _insert_spikes(compresseur["current"].to_numpy(), 0.08, 1.4, 2.1)

    echangeur = pd.DataFrame(
        {
            "timestamp": timestamps,
            "temp_in_hot": np.random.normal(96.0, 2.5, ROWS_PER_FILE),
            "temp_out_hot": np.random.normal(72.0, 2.4, ROWS_PER_FILE),
            "temp_in_cold": np.random.normal(22.0, 1.5, ROWS_PER_FILE),
            "temp_out_cold": np.random.normal(38.0, 1.9, ROWS_PER_FILE),
            "flow_rate": np.random.normal(152.0, 10.0, ROWS_PER_FILE),
        }
    )
    echangeur["temp_in_hot"] = _insert_spikes(
        echangeur["temp_in_hot"].to_numpy(), 0.06, 1.15, 1.35
    )
    echangeur["flow_rate"] = _insert_spikes(echangeur["flow_rate"].to_numpy(), 0.06, 0.7, 0.9)

    for machine_name, frame in {
        "moteur": moteur,
        "pompe": pompe,
        "compresseur": compresseur,
        "echangeur": echangeur,
    }.items():
        frame = frame.round(4)
        frame.to_csv(DATA_DIR / f"{machine_name}.csv", index=False)


def publish_machine_row(machine, row):
    timestamp = row.get("timestamp")
    sensors = {k: v for k, v in row.items() if k != "timestamp"}
    payload = {"machine": machine, "sensors": sensors, "timestamp": timestamp}

    redis_client.publish(CHANNEL_NAME, json.dumps(payload))

    with state_lock:
        service_state["last_received"][machine] = timestamp


def replay_csv(machine):
    path = DATA_DIR / f"{machine}.csv"
    while True:
        frame = pd.read_csv(path)
        rows = frame.to_dict(orient="records")
        for row in rows:
            publish_machine_row(machine, row)
            time.sleep(REPLAY_INTERVAL_SECONDS)


def start_replay_threads():
    for machine in service_state["last_received"].keys():
        thread = threading.Thread(target=replay_csv, args=(machine,), daemon=True)
        thread.start()


@app.route("/api/iot/status", methods=["GET"])
def status():
    with state_lock:
        return jsonify(
            {
                "mode": service_state["mode"],
                "last_received": service_state["last_received"],
            }
        )


@app.route("/api/iot/inject", methods=["POST"])
def inject():
    body = request.get_json(silent=True) or {}
    machine = body.get("machine")
    sensors = body.get("sensors")
    timestamp = body.get("timestamp") or datetime.utcnow().isoformat()

    if machine not in service_state["last_received"]:
        return jsonify({"error": "Invalid machine."}), 400
    if not isinstance(sensors, dict):
        return jsonify({"error": "sensors must be an object."}), 400

    payload = {"machine": machine, "sensors": sensors, "timestamp": timestamp}
    redis_client.publish(CHANNEL_NAME, json.dumps(payload))

    with state_lock:
        service_state["last_received"][machine] = timestamp

    return jsonify({"message": "Injected", "payload": payload}), 201


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "iot"})


generate_csv_files()
start_replay_threads()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
