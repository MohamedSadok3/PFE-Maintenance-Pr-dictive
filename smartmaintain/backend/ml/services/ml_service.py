import json
import logging
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

logger = logging.getLogger(__name__)


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

    def reload_models(self, machine: str = None) -> dict:
        """
        Hot-reload ML models without restarting the service.
        
        This allows deploying newly trained models from Colab without downtime.
        
        Args:
            machine: Specific machine to reload, or None to reload all
        
        Returns:
            dict with reload status and any errors
        """
        if self.mock_ml:
            return {
                "success": False,
                "message": "Model reload not available in mock mode",
            }

        try:
            logger.info(f"Hot-reloading models for: {machine or 'all machines'}")
            
            # Create a new engine instance (forces model reload from disk)
            new_engine = RealMLEngine()
            
            if machine:
                # Verify the specific machine model loaded successfully
                if machine not in new_engine.models:
                    return {
                        "success": False,
                        "message": f"Failed to load model for {machine}",
                        "machine": machine,
                    }
                
                # Replace only the specific machine's model
                if hasattr(self.engine, 'models'):
                    self.engine.models[machine] = new_engine.models[machine]
                    self.engine.scalers[machine] = new_engine.scalers[machine]
                    self.engine.label_encoders[machine] = new_engine.label_encoders[machine]
                    self.engine.metadata[machine] = new_engine.metadata[machine]
                
                logger.info(f"✅ Successfully reloaded model for {machine}")
                
                return {
                    "success": True,
                    "message": f"Model for {machine} reloaded successfully",
                    "machine": machine,
                    "model_name": self.active_models.get(machine),
                    "accuracy": new_engine.metadata.get(machine, {}).get("accuracy"),
                }
            else:
                # Replace entire engine (reload all models)
                self.engine = new_engine
                
                loaded_machines = list(self.engine.models.keys())
                logger.info(f"✅ Successfully reloaded models for: {loaded_machines}")
                
                return {
                    "success": True,
                    "message": f"All models reloaded successfully",
                    "loaded_machines": loaded_machines,
                    "count": len(loaded_machines),
                }
        
        except Exception as e:
            logger.error(f"❌ Failed to reload models: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Model reload failed: {str(e)}",
                "machine": machine,
            }

    def _build_prediction_payload(self, machine, prediction, timestamp=None, plant_id=None, sensors=None):
        payload = {
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
        # Pass raw sensor readings through so the frontend surveillance charts
        # can plot live values directly from the sensor:data WebSocket event.
        # Without this, the frontend receives the ML prediction but has no sensor
        # values to render in the charts.
        if sensors:
            payload["sensors"] = sensors
        # Propagate plant_id from the IoT payload so the Alertes service can
        # assign the alert to the correct plant without a database look-up.
        if plant_id is not None:
            payload["plant_id"] = plant_id
        return payload

    def predict_for_machine(self, machine, sensors, plant_id=None, component_id=None, log_prediction=True):
        """
        Make a prediction for a specific machine.
        
        Args:
            machine: Machine type
            sensors: Sensor readings
            plant_id: Optional plant identifier
            component_id: Optional component identifier
            log_prediction: Whether to log prediction for fine-tuning (default: True)
        """
        if machine not in self.supported_models:
            return {"error": "Unsupported machine."}, 400

        try:
            prediction = self.engine.predict(machine, sensors)
            payload = self._build_prediction_payload(
                machine, prediction, plant_id=plant_id, sensors=sensors
            )
            
            # Asynchronously log prediction for fine-tuning
            if log_prediction:
                self._log_prediction_async(
                    machine=machine,
                    sensors=sensors,
                    prediction=prediction,
                    payload=payload,
                    plant_id=plant_id,
                    component_id=component_id,
                )
            
            return payload, 200
        except Exception as e:
            return {"error": f"Prediction failed: {str(e)}"}, 500

    def _log_prediction_async(self, machine, sensors, prediction, payload, plant_id=None, component_id=None):
        """
        Log prediction asynchronously to avoid blocking the prediction response.
        
        This stores the prediction in the database for future fine-tuning.
        Failures in logging don't affect the prediction response.
        """
        try:
            from services.feedback_service import FeedbackService
            
            feedback_service = FeedbackService()
            feedback_service.log_prediction(
                machine=machine,
                sensors=sensors,
                predicted_defect=prediction["defect"],
                defect_score=prediction["defect_score"],
                confidence=prediction["confidence"],
                defect_scores=prediction.get("defect_scores", {}),
                model_name=payload.get("model_name", "unknown"),
                timestamp=payload.get("timestamp"),
                plant_id=plant_id,
                component_id=component_id,
            )
        except Exception as e:
            # Don't fail the prediction if logging fails
            logger.warning(f"Failed to log prediction for fine-tuning: {e}")

    def finetune_model(self, machine, model_name):
        """
        Update the active model name for a machine (mock mode only).
        Real training is handled by FineTuneService.submit_job().
        """
        if machine not in self.supported_models:
            return {"error": "Unsupported machine."}, 400

        if self.mock_ml:
            self.active_models[machine] = model_name
            return {
                "jobId":      ML_DEFAULT_MOCK_JOB_ID,
                "message":    "Nom du modèle mis à jour (mode mock).",
                "machine":    machine,
                "model_name": model_name,
            }, 200

        # Real mode: caller should use FineTuneService.submit_job() with a CSV.
        self.active_models[machine] = model_name
        return {
            "message":    f"Modèle actif mis à jour pour '{machine}' → '{model_name}'. "
                          "Aucun réentraînement effectué. "
                          "Utilisez POST /api/ml/finetune avec un fichier CSV pour réentraîner.",
            "machine":    machine,
            "model_name": model_name,
        }, 200

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
                payload   = json.loads(message.get("data", "{}"))
                machine   = payload.get("machine")
                sensors   = payload.get("sensors", {})
                timestamp = payload.get("timestamp") or datetime.now(timezone.utc).isoformat()
                plant_id  = payload.get("plant_id")
                component_id = payload.get("component_id")

                if machine not in self.supported_models:
                    continue

                prediction = self.engine.predict(machine, sensors)
                ml_payload = self._build_prediction_payload(
                    machine, prediction, timestamp=timestamp, plant_id=plant_id, sensors=sensors
                )
                
                # Log prediction for fine-tuning
                self._log_prediction_async(
                    machine=machine,
                    sensors=sensors,
                    prediction=prediction,
                    payload=ml_payload,
                    plant_id=plant_id,
                    component_id=component_id,
                )
                
                self.redis_client.publish(REDIS_ML_PREDICTIONS_CHANNEL, json.dumps(ml_payload))
            except Exception:
                # Keep stream consumer resilient
                continue
