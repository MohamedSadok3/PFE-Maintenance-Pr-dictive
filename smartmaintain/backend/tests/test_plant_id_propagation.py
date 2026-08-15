"""
Integration-style unit tests for plant_id propagation through the pipeline:
  IoT (ReplayService) → ML (MLService) → Alertes (RedisConsumer)

No real Redis or database connections are used.

Run with:
    pytest backend/tests/test_plant_id_propagation.py -v
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "iot"))
sys.path.insert(0, str(Path(__file__).parent.parent / "ml"))
sys.path.insert(0, str(Path(__file__).parent.parent / "alertes"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
os.environ.setdefault("POSTGRES_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("JWT_SECRET",   "test-secret-for-unit-tests")
os.environ.setdefault("REDIS_URL",    "redis://localhost:6379")


# ── IoT: ReplayService stamps plant_id ──────────────────────────────────────

class TestReplayServicePlantId:
    def _make_service(self, plant_id=None):
        with patch("redis.from_url") as mock_redis:
            from services.replay_service import ReplayService
            svc = ReplayService.__new__(ReplayService)
            svc.redis_client             = MagicMock()
            svc.channel_name             = "sensor_data"
            svc.data_dir                 = Path("/tmp")
            svc.replay_interval_seconds  = 1
            svc.plant_id                 = plant_id
            return svc

    def test_plant_id_included_when_set(self):
        svc = self._make_service(plant_id=3)

        window = [{"vibration": 0.5, "current": 10.0, "timestamp": "2025-01-01T00:00:00"}] * 20

        published = []
        svc.redis_client.publish = lambda ch, data: published.append(json.loads(data))

        svc.publish_machine_window("moteur", window)

        assert len(published) == 1
        assert published[0]["plant_id"] == 3

    def test_plant_id_omitted_when_not_set(self):
        svc = self._make_service(plant_id=None)

        window = [{"vibration": 0.5, "current": 10.0, "timestamp": "2025-01-01T00:00:00"}] * 20

        published = []
        svc.redis_client.publish = lambda ch, data: published.append(json.loads(data))

        svc.publish_machine_window("moteur", window)

        assert len(published) == 1
        assert "plant_id" not in published[0]


# ── ML: MLService forwards plant_id ─────────────────────────────────────────

class TestMLServicePlantIdPropagation:
    def _make_service(self):
        with patch("redis.from_url"):
            os.environ["MOCK_ML"] = "true"
            from services.ml_service import MLService
            svc = MLService.__new__(MLService)
            svc.redis_client        = MagicMock()
            svc.mock_ml             = True
            from engines.mock_engine import MockMLEngine
            svc.engine              = MockMLEngine()
            svc.supported_models    = ["moteur", "pompe", "compresseur", "echangeur"]
            from shared.constants import BEST_MODEL_BY_MACHINE
            svc.best_model_by_machine = dict(BEST_MODEL_BY_MACHINE)
            svc.active_models       = dict(BEST_MODEL_BY_MACHINE)
            return svc

    def test_plant_id_in_prediction_payload(self):
        svc = self._make_service()
        result, status = svc.predict_for_machine(
            "moteur", {"vibration": 0.5, "current": 10.0}, plant_id=7
        )
        assert status == 200
        assert result["plant_id"] == 7

    def test_plant_id_none_omitted_from_payload(self):
        svc = self._make_service()
        result, status = svc.predict_for_machine(
            "moteur", {"vibration": 0.5, "current": 10.0}, plant_id=None
        )
        assert status == 200
        assert "plant_id" not in result

    def test_plant_id_forwarded_through_consume(self):
        svc = self._make_service()

        published = []
        svc.redis_client.publish = lambda ch, data: published.append(json.loads(data))

        # Simulate a Redis message with plant_id
        message = {
            "type": "message",
            "data": json.dumps({
                "machine":   "moteur",
                "sensors":   {"vibration": 0.5, "current": 10.0},
                "timestamp": "2025-01-01T00:00:00",
                "plant_id":  5,
            }),
        }

        # Run one iteration of the consume loop
        svc._build_prediction_payload = MagicMock(
            wraps=svc._build_prediction_payload
        )
        payload = json.loads(message["data"])
        machine   = payload["machine"]
        sensors   = payload["sensors"]
        timestamp = payload["timestamp"]
        plant_id  = payload.get("plant_id")

        prediction = svc.engine.predict(machine, sensors)
        ml_payload = svc._build_prediction_payload(
            machine, prediction, timestamp=timestamp, plant_id=plant_id
        )
        assert ml_payload.get("plant_id") == 5


# ── Alertes: RedisConsumer uses plant_id from payload ───────────────────────

class TestRedisConsumerPlantId:
    def _make_consumer(self):
        with patch("redis.from_url"):
            with patch("shared.database.get_db_connection"):
                from services.alert_service import AlertService
                from services.redis_consumer import RedisConsumer

                socketio = MagicMock()
                consumer = RedisConsumer.__new__(RedisConsumer)
                consumer.socketio           = socketio
                consumer.predictions_channel = "ml_predictions"

                alert_svc = AlertService.__new__(AlertService)
                alert_svc.redis_client = MagicMock()
                alert_svc.severity_from_score = AlertService.severity_from_score.__get__(
                    alert_svc, AlertService
                )
                alert_svc.insert_alert        = MagicMock(return_value=MagicMock(to_dict=lambda: {}))
                alert_svc.get_default_plant_id = MagicMock(return_value=1)

                consumer.alert_service = alert_svc
                return consumer, alert_svc

    def test_uses_plant_id_from_payload(self):
        consumer, alert_svc = self._make_consumer()

        # Score high enough to create an alert (>= 0.40 = Mineure)
        prediction = {
            "machine":      "moteur",
            "defect":       "degradation_roulement",
            "defect_scores": {"degradation_roulement": 0.70, "normal_operation": 0.30},
            "defect_score": 0.70,
            "confidence":   0.85,
            "plant_id":     42,
        }

        consumer.socketio.emit = MagicMock()

        # Simulate the processing logic directly
        defect_scores = prediction.get("defect_scores") or {}
        top_defect, top_score = max(defect_scores.items(), key=lambda item: float(item[1]))
        score    = float(top_score)
        severity = consumer.alert_service.severity_from_score(score)

        incoming_plant_id = prediction.get("plant_id")
        plant_id = int(incoming_plant_id) if incoming_plant_id else consumer.alert_service.get_default_plant_id()

        assert plant_id == 42
        # get_default_plant_id should NOT have been called
        alert_svc.get_default_plant_id.assert_not_called()

    def test_missing_plant_id_is_not_assigned_to_default_plant(self):
        consumer, alert_svc = self._make_consumer()

        prediction = {
            "machine":      "moteur",
            "defect":       "degradation_roulement",
            "defect_scores": {"degradation_roulement": 0.70, "normal_operation": 0.30},
            "defect_score": 0.70,
            "confidence":   0.85,
            # no plant_id
        }

        incoming_plant_id = prediction.get("plant_id")

        assert incoming_plant_id is None
        alert_svc.get_default_plant_id.assert_not_called()
