import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import numpy as np
import pytest
from flask import Flask

ML_DIR = Path(__file__).parent.parent / "ml"
sys.path.insert(0, str(ML_DIR))
sys.path.insert(0, str(ML_DIR / "services"))

from engines.real_engine import RealMLEngine
from routes.predict import ml_bp
from routes.status import status_bp
from ml_service import MLService
from model_service import ModelService


class FakeRedis:
    def publish(self, *_args, **_kwargs):
        return 1


@pytest.fixture(scope="module")
def api_client():
    registry = ModelService(ML_DIR / "models_v7")
    service = MLService(engine=RealMLEngine(registry), redis_client=FakeRedis())
    app = Flask(__name__)
    app.extensions["ml_service"] = service
    app.register_blueprint(ml_bp, url_prefix="/api/ml")
    app.register_blueprint(status_bp, url_prefix="/api/ml/status")
    return app.test_client(), registry


def auth_headers():
    token = jwt.encode(
        {"sub": "1", "role": "admin", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "test-secret-key-for-unit-tests-only",
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def test_prediction_api(api_client):
    client, registry = api_client
    bundle = registry.get_bundle("echangeur")
    response = client.post(
        "/api/ml/predict",
        json={"equipment_type": "echangeur", "features": {name: 0.0 for name in bundle.feature_names}},
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert response.get_json()["equipment_type"] == "echangeur"


def test_prediction_api_missing_feature(api_client):
    client, _ = api_client
    response = client.post(
        "/api/ml/predict",
        json={"equipment_type": "moteur", "features": {}},
        headers=auth_headers(),
    )
    assert response.status_code == 422
    assert response.get_json()["error"] == "missing_features"


def api_series(registry, machine, size):
    bundle = registry.get_bundle(machine)
    signals = {registry._split(name)[0] for name in bundle.feature_names}
    return {signal: list(np.linspace(1.0, 2.0, size)) for signal in signals}


def test_api_returns_202_for_incomplete_compressor_window(api_client):
    client, registry = api_client
    response = client.post(
        "/api/ml/predict",
        json={"equipment_type": "compresseur", "series": api_series(registry, "compresseur", 20)},
        headers=auth_headers(),
    )
    assert response.status_code == 202
    assert response.get_json() == {
        "error": "acquisition_insuffisante",
        "message": "Acquisition insuffisante: la fenêtre temporelle n’est pas complète.",
        "machine": "compresseur",
        "received": 20,
        "required": 30,
        "status": "acquisition_continue",
    }


def test_api_rejects_motor_series(api_client):
    client, _ = api_client
    response = client.post(
        "/api/ml/predict",
        json={"equipment_type": "moteur", "series": {"vibration": [1.0] * 30}},
        headers=auth_headers(),
    )
    assert response.status_code == 422
    assert response.get_json()["error"] == "unsupported_raw_input"


def test_status_exposes_complete_model_contract(api_client):
    client, _ = api_client
    response = client.get("/api/ml/status", headers=auth_headers())
    assert response.status_code == 200
    bundles = response.get_json()["bundles"]
    assert bundles["moteur"]["supported_input_types"] == ["features"]
    assert bundles["moteur"]["required_window_size"] is None
    assert bundles["pompe"]["required_window_size"] == 20
    assert bundles["compresseur"]["required_window_size"] == 30
    assert bundles["echangeur"]["required_window_size"] == 30
    for status in bundles.values():
        assert {
            "loaded", "version", "classes", "feature_count", "required_window_size",
            "supported_input_types", "robustness_accuracy", "clean_accuracy",
            "warnings", "provenance", "estimator_type",
        } <= set(status)
