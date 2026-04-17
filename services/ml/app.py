import json
import os
import threading
from datetime import datetime, timezone

import redis
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from mock_engine import MockMLEngine

load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
MOCK_ML = os.environ.get("MOCK_ML", "true").lower() == "true"
PORT = 5002
INPUT_CHANNEL = "sensor_data"
OUTPUT_CHANNEL = "ml_predictions"
SUPPORTED_MODELS = ["moteur", "pompe", "compresseur", "echangeur"]
BEST_MODEL_BY_MACHINE = {
    "moteur": "LSTM-moteur-v2",
    "pompe": "LSTM-pompe-v2",
    "compresseur": "Transformer-compresseur-v1",
    "echangeur": "LSTM-echangeur-v2",
}

app = Flask(__name__)
CORS(app)

redis_client = redis.from_url(REDIS_URL, decode_responses=True)


class RealMLEngine:
    """
    Placeholder for future real-model mode.
    Keep the same public interface as MockMLEngine so no route/consumer changes are required.
    """

    def __init__(self):
        self.models = self._load_models()

    def _load_models(self):
        # Future implementation example:
        # import tensorflow as tf
        # return {
        #   "moteur": tf.keras.models.load_model("/app/models/moteur.h5"),
        #   ...
        # }
        raise NotImplementedError("Real model loading is not implemented yet.")

    def predict(self, machine, sensors):
        raise NotImplementedError("Real model prediction is not implemented yet.")


def build_engine():
    if MOCK_ML:
        return MockMLEngine()
    return RealMLEngine()


engine = build_engine()
ACTIVE_MODELS = {machine: BEST_MODEL_BY_MACHINE[machine] for machine in SUPPORTED_MODELS}


def predict_for_machine(machine, sensors):
    if machine not in SUPPORTED_MODELS:
        return {"error": "Unsupported machine."}, 400

    prediction = engine.predict(machine, sensors)
    response = {
        "machine": machine,
        "defect_score": prediction["defect_score"],
        "anomaly_score": prediction["defect_score"],
        "defect": prediction["defect"],
        "defect_scores": prediction.get("defect_scores", {}),
        "confidence": prediction["confidence"],
        "required_sensors": prediction.get("required_sensors", []),
        "model_name": ACTIVE_MODELS.get(machine, BEST_MODEL_BY_MACHINE.get(machine)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return response, 200


def consume_sensor_data():
    pubsub = redis_client.pubsub()
    pubsub.subscribe(INPUT_CHANNEL)

    for message in pubsub.listen():
        if message.get("type") != "message":
            continue

        try:
            payload = json.loads(message.get("data", "{}"))
            machine = payload.get("machine")
            sensors = payload.get("sensors", {})
            timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()

            if machine not in SUPPORTED_MODELS:
                continue

            prediction = engine.predict(machine, sensors)
            ml_payload = {
                "machine": machine,
                "defect_score": prediction["defect_score"],
                "anomaly_score": prediction["defect_score"],
                "defect": prediction["defect"],
                "defect_scores": prediction.get("defect_scores", {}),
                "confidence": prediction["confidence"],
                "required_sensors": prediction.get("required_sensors", []),
                "model_name": ACTIVE_MODELS.get(machine, BEST_MODEL_BY_MACHINE.get(machine)),
                "timestamp": timestamp,
            }
            redis_client.publish(OUTPUT_CHANNEL, json.dumps(ml_payload))
        except Exception:
            # Keep stream consumer resilient; malformed messages should not kill the worker.
            continue


@app.route("/api/ml/status", methods=["GET"])
def status():
    return jsonify({"mock_mode": MOCK_ML, "models": SUPPORTED_MODELS})


@app.route("/api/ml/predict", methods=["POST"])
def predict():
    body = request.get_json(silent=True) or {}
    machine = body.get("machine")
    sensors = body.get("sensors")

    if not machine or not isinstance(sensors, dict):
        return jsonify({"error": "machine and sensors are required."}), 400

    response, status_code = predict_for_machine(machine, sensors)
    return jsonify(response), status_code


@app.route("/api/ml/finetune", methods=["POST"])
def finetune():
    body = request.get_json(silent=True) or {}
    machine = body.get("machine")
    model_name = body.get("model_name")

    if machine not in SUPPORTED_MODELS:
        return jsonify({"error": "Unsupported machine."}), 400
    if not model_name:
        return jsonify({"error": "model_name is required."}), 400

    ACTIVE_MODELS[machine] = model_name
    return jsonify({"jobId": "mock-job-1", "message": "Model updated in mock mode", "machine": machine, "model_name": model_name})


@app.route("/api/ml/finetune/status/<job_id>", methods=["GET"])
def finetune_status(job_id):
    return jsonify({"status": "not_available"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ml", "mock_mode": MOCK_ML})


consumer_thread = threading.Thread(target=consume_sensor_data, daemon=True)
consumer_thread.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
