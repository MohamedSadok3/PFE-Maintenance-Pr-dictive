"""
RealMLEngine — Modèle XGBoost pour SmartMaintain
=================================================
Charge les modèles depuis /app/models/ et prédit les défauts moteur.
Interface identique à MockMLEngine — aucun changement ailleurs.
"""

import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import skew, kurtosis

from .base_engine import BaseMLEngine

logger = logging.getLogger(__name__)

# Mapping labels SmartMaintain → classes CWRU
LABEL_TO_SMARTMAINTAIN = {
    "normal_operation":          "normal_operation",
    "degradation_roulement":     "degradation_roulement",
    "desequilibre_desalignement":"desequilibre_desalignement",
}

REQUIRED_SENSORS_MAP = {
    "moteur":      ["vibration", "current"],
    "pompe":       ["vibration", "pressure_in", "pressure_out"],
    "compresseur": ["pressure", "current"],
    "echangeur":   ["temp_in_hot", "temp_out_hot", "flow_rate"],
}

FEATURE_NAMES = ['max', 'min', 'mean', 'sd', 'rms', 'skewness', 'kurtosis', 'crest', 'form']


class RealMLEngine(BaseMLEngine):
    """
    Moteur ML utilisant XGBoost pré-entraîné sur CWRU dataset.
    Interface identique à MockMLEngine.
    """

    MODELS_DIR = Path("/app/models")

    def __init__(self):
        self.models         = {}
        self.scalers        = {}
        self.label_encoders = {}
        self.metadata       = {}
        self._load_all_models()

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def _load_all_models(self):
        try:
            self.models["moteur"]         = joblib.load(self.MODELS_DIR / "moteur_xgb.pkl")
            self.scalers["moteur"]        = joblib.load(self.MODELS_DIR / "moteur_scaler.pkl")
            self.label_encoders["moteur"] = joblib.load(self.MODELS_DIR / "moteur_label_encoder.pkl")
            with open(self.MODELS_DIR / "moteur_metadata.json") as f:
                self.metadata["moteur"] = json.load(f)
            logger.info(
                f"[RealMLEngine] Modèle moteur chargé — "
                f"accuracy={self.metadata['moteur'].get('accuracy', 'N/A')}"
            )
        except FileNotFoundError as e:
            logger.error(f"[RealMLEngine] Fichier introuvable : {e}")
        except Exception as e:
            logger.error(f"[RealMLEngine] Erreur chargement : {e}")

    # ------------------------------------------------------------------
    # Interface publique (identique à MockMLEngine)
    # ------------------------------------------------------------------

    def predict(self, machine: str, sensors: dict) -> dict:
        machine = (machine or "").lower()
        if machine not in self.models:
            logger.warning(f"[RealMLEngine] Modèle non disponible pour '{machine}'")
            return self._fallback(machine)
        try:
            features = self._extract_features(machine, sensors)
            return self._run_prediction(machine, features)
        except Exception as e:
            logger.error(f"[RealMLEngine] Erreur prédiction '{machine}': {e}")
            return self._fallback(machine)

    # ------------------------------------------------------------------
    # Extraction des features
    # ------------------------------------------------------------------

    def _extract_features(self, machine: str, sensors: dict) -> pd.DataFrame:
        """
        Construit le vecteur de 9 features depuis les données sensors.
        
        Le service IoT envoie maintenant des features pré-calculées sur une fenêtre :
        vibration_max, vibration_min, vibration_mean, vibration_sd, vibration_rms,
        vibration_skewness, vibration_kurtosis, vibration_crest, vibration_form
        
        Si ces features ne sont pas disponibles, fallback sur vibration_instant.
        """
        # Cas 1 : IoT envoie les features pré-calculées (mode production)
        if "vibration_rms" in sensors:
            values = [
                float(sensors.get("vibration_max",      0.0)),
                float(sensors.get("vibration_min",      0.0)),
                float(sensors.get("vibration_mean",     0.0)),
                float(sensors.get("vibration_sd",       0.0)),
                float(sensors.get("vibration_rms",      0.0)),
                float(sensors.get("vibration_skewness", 0.0)),
                float(sensors.get("vibration_kurtosis", 0.0)),
                float(sensors.get("vibration_crest",    1.0)),
                float(sensors.get("vibration_form",     1.0)),
            ]
            return pd.DataFrame([values], columns=FEATURE_NAMES)

        # Cas 2 : IoT envoie une valeur scalaire (mode mock/fallback)
        # Construire une approximation des features
        v = float(sensors.get("vibration", 0.0))
        c = float(sensors.get("current",   0.0))

        # Simuler un signal court depuis la valeur scalaire
        signal = np.array([v, -v*0.3, v*0.7, -v*0.5, c/20,
                           v*0.9, -v*0.2, v*0.6, -v*0.4,
                           v*0.8, -v*0.4, v*0.5, -v*0.3, v*0.7])

        rms      = float(np.sqrt(np.mean(signal**2)))
        mean_abs = float(np.mean(np.abs(signal)))

        values = [
            float(np.max(signal)),
            float(np.min(signal)),
            float(np.mean(signal)),
            float(np.std(signal)),
            rms,
            float(skew(signal)),
            float(kurtosis(signal)),
            float(np.max(np.abs(signal))) / (rms + 1e-10),
            rms / (mean_abs + 1e-10),
        ]
        return pd.DataFrame([values], columns=FEATURE_NAMES)

    # ------------------------------------------------------------------
    # Prédiction
    # ------------------------------------------------------------------

    def _run_prediction(self, machine: str, features: pd.DataFrame) -> dict:
        scaler        = self.scalers[machine]
        model         = self.models[machine]
        label_encoder = self.label_encoders[machine]

        features_scaled = scaler.transform(features)
        proba           = model.predict_proba(features_scaled)[0]
        predicted_idx   = int(np.argmax(proba))

        defect_name = label_encoder.inverse_transform([predicted_idx])[0]
        confidence  = float(proba[predicted_idx])

        # defect_score = 1 - P(normal_operation)
        try:
            normal_idx   = list(label_encoder.classes_).index("normal_operation")
            defect_score = float(1.0 - proba[normal_idx])
        except ValueError:
            defect_score = float(1.0 - proba[0])

        # Scores par classe
        defect_scores = {
            cls: round(float(p), 4)
            for cls, p in zip(label_encoder.classes_, proba)
        }

        required = (
            REQUIRED_SENSORS_MAP.get(machine, [])
            if defect_name != "normal_operation" else []
        )

        return {
            "defect_score":     round(defect_score, 4),
            "anomaly_score":    round(defect_score, 4),
            "defect":           defect_name,
            "defect_scores":    defect_scores,
            "confidence":       round(confidence, 4),
            "required_sensors": required,
        }

    def _fallback(self, machine: str) -> dict:
        return {
            "defect_score":     0.0,
            "anomaly_score":    0.0,
            "defect":           "normal_operation",
            "defect_scores":    {"normal_operation": 1.0},
            "confidence":       0.5,
            "required_sensors": REQUIRED_SENSORS_MAP.get(machine, []),
        }
