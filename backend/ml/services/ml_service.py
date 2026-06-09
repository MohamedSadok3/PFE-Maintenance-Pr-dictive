import json
from datetime import datetime, timezone

import redis

from shared.config import get_env
from shared.constants import (
    BEST_MODEL_BY_MACHINE,
    MACHINE_TYPES,
    ML_DEFAULT_MOCK_JOB_ID,
    MOCK_ML_DEFAULT_ENABLED,
    REDIS_DEFAULT_URL,
    REDIS_ML_PREDICTIONS_CHANNEL,
    REDIS_SENSOR_CHANNEL,
)
from engines.mock_engine import MockMLEngine
from engines.real_engine import RealMLEngine


class MLService:
    """Service for ML predictions and model management."""

    def __init__(self):
        self.redis_client = redis.from_url(
            get_env("REDIS_URL", REDIS_DEFAULT_URL), decode_responses=True
        )
        self.mock_ml = (
            get_env("MOCK_ML", str(MOCK_ML_DEFAULT_ENABLED).lower()).lower() == "true"
        )
        self.engine = self._build_engine()
        self.supported_models = MACHINE_TYPES
        self.best_model_by_machine = dict(BEST_MODEL_BY_MACHINE)
        self.active_models = {
            machine: self.best_model_by_machine[machine]
            for machine in self.supported_models
        }

    def _build_engine(self):
        """Build the appropriate ML engine based on configuration."""
        if self.mock_ml:
            return MockMLEngine()
        return RealMLEngine()

    def _build_prediction_payload(self, machine, prediction, timestamp=None):
        return {
            "machine": machine,
            "defect_score": prediction["defect_score"],
            "anomaly_score": prediction["defect_score"],
            "defect": prediction["defect"],
            "defect_scores": prediction.get("defect_scores", {}),
            "confidence": prediction["confidence"],
            "required_sensors": prediction.get("required_sensors", []),
            "model_name": self.active_models.get(machine, self.best_model_by_machine.get(machine)),
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        }

    def predict_for_machine(self, machine, sensors):
        """Make a prediction for a specific machine."""
        if machine not in self.supported_models:
            return {"error": "Unsupported machine."}, 400

        try:
            prediction = self.engine.predict(machine, sensors)
            return self._build_prediction_payload(machine, prediction), 200
        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}, 500

    def finetune_model(self, machine, model_name):
        """Fine-tune a model for a specific machine."""
        if machine not in self.supported_models:
            return {"error": "Unsupported machine."}, 400

        # In mock mode, just update the active model
        if self.mock_ml:
            self.active_models[machine] = model_name
            return {
                "jobId": ML_DEFAULT_MOCK_JOB_ID,
                "message": "Model updated in mock mode",
                "machine": machine,
                "model_name": model_name
            }, 200

        # TODO: Implement real fine-tuning job
        return {"error": "Real fine-tuning not implemented yet."}, 501

    def get_finetune_status(self, job_id):
        """Get the status of a fine-tuning job."""
        # Mock implementation
        return {"status": "not_available"}, 200

    def get_status(self):
        """Get service status and available models."""
        return {
            "mock_mode": self.mock_ml,
            "models": self.supported_models,
            "active_models": self.active_models
        }

    def consume_sensor_data(self):
        """Consume sensor data from Redis and publish predictions."""
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(REDIS_SENSOR_CHANNEL)

        for message in pubsub.listen():
            if message.get("type") != "message":
                continue

            try:
                payload = json.loads(message.get("data", "{}"))
                machine = payload.get("machine")
                sensors = payload.get("sensors", {})
                timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()

                if machine not in self.supported_models:
                    continue

                prediction = self.engine.predict(machine, sensors)
                ml_payload = self._build_prediction_payload(machine, prediction, timestamp=timestamp)
                self.redis_client.publish(REDIS_ML_PREDICTIONS_CHANNEL, json.dumps(ml_payload))
            except Exception:
                # Keep stream consumer resilient
                continue