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

# Mapping CWRU raw class labels → SmartMaintain defect names.
# The model was trained on raw CWRU labels (Ball_007_1, IR_007_1, Normal_1, etc.)
# so we map them to the canonical names used across the platform.
CWRU_TO_SMARTMAINTAIN = {
    "Normal_1": "normal_operation",
    # Ball fault (rolling element)
    "Ball_007_1": "degradation_roulement",
    "Ball_014_1": "degradation_roulement",
    "Ball_021_1": "degradation_roulement",
    # Inner race fault
    "IR_007_1": "degradation_roulement",
    "IR_014_1": "degradation_roulement",
    "IR_021_1": "degradation_roulement",
    # Outer race fault
    "OR_007_6_1": "degradation_roulement",
    "OR_014_6_1": "degradation_roulement",
    "OR_021_6_1": "degradation_roulement",
    # Keep SmartMaintain labels as-is if the model was retrained on them
    "normal_operation":           "normal_operation",
    "degradation_roulement":      "degradation_roulement",
    "desequilibre_desalignement": "desequilibre_desalignement",
}

def _map_class(raw_label: str) -> str:
    """Map a raw model class label to a SmartMaintain defect name."""
    return CWRU_TO_SMARTMAINTAIN.get(raw_label, raw_label)

REQUIRED_SENSORS_MAP = {
    "moteur":      ["vibration", "current"],
    "pompe":       ["vibration", "pressure_in", "pressure_out"],
    "compresseur": ["pressure", "current"],
    "echangeur":   ["temp_in_hot", "temp_out_hot", "flow_rate"],
}

FEATURE_NAMES = ["max", "min", "mean", "sd", "rms", "skewness", "kurtosis", "crest", "form"]

# Files required per machine.  Each entry lists (relative_name, description).
_REQUIRED_FILES = {
    "moteur": [
        ("moteur_xgb.pkl",           "XGBoost model"),
        ("moteur_scaler.pkl",        "StandardScaler"),
        ("moteur_label_encoder.pkl", "LabelEncoder"),
        ("moteur_metadata.json",     "metadata"),
    ],
    "pompe": [
        ("pompe_xgb.pkl",           "XGBoost model"),
        ("pompe_scaler.pkl",        "StandardScaler"),
        ("pompe_label_encoder.pkl", "LabelEncoder"),
        ("pompe_metadata.json",     "metadata"),
    ],
    "compresseur": [
        ("compresseur_xgb.pkl",           "XGBoost model"),
        ("compresseur_scaler.pkl",        "StandardScaler"),
        ("compresseur_label_encoder.pkl", "LabelEncoder"),
        ("compresseur_metadata.json",     "metadata"),
    ],
    "echangeur": [
        ("echangeur_xgb.pkl",           "XGBoost model"),
        ("echangeur_scaler.pkl",        "StandardScaler"),
        ("echangeur_label_encoder.pkl", "LabelEncoder"),
        ("echangeur_metadata.json",     "metadata"),
    ],
}


class RealMLEngine(BaseMLEngine):
    """
    Moteur ML utilisant XGBoost pré-entraîné sur CWRU dataset.
    Interface identique à MockMLEngine.
    """

    MODELS_DIR = Path("/app/models/trained")

    def __init__(self):
        self.models         = {}
        self.scalers        = {}
        self.label_encoders = {}
        self.metadata       = {}
        self._validate_model_files()
        self._load_all_models()

    # ------------------------------------------------------------------
    # Validation au démarrage
    # ------------------------------------------------------------------

    def _validate_model_files(self) -> None:
        """
        Vérifie que tous les fichiers de modèle requis sont présents avant de
        tenter de les charger.  Émet une erreur explicite pour chaque fichier
        manquant afin de faciliter le diagnostic.
        """
        missing = []
        for machine, files in _REQUIRED_FILES.items():
            for filename, description in files:
                path = self.MODELS_DIR / filename
                if not path.exists():
                    missing.append(f"  [{machine}] {filename} ({description}) — attendu à {path}")

        if missing:
            message = (
                "[RealMLEngine] Fichiers de modèle requis manquants :\n"
                + "\n".join(missing)
                + "\n\n Veuillez entraîner les modèles avec :\n"
                "       python backend/ml/models/train_model.py"
            )
            logger.error(message)
            raise FileNotFoundError(f"Modèles ML manquants : {', '.join(missing)}")

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def _load_all_models(self) -> None:
        """Tente de charger tous les modèles disponibles.  Continue si un modèle est absent."""
        logger.info("[RealMLEngine] Début chargement des modèles depuis %s", self.MODELS_DIR)
        
        for machine, files in _REQUIRED_FILES.items():
            logger.info("[RealMLEngine] Tentative de chargement du modèle '%s'...", machine)
            try:
                paths = {filename: self.MODELS_DIR / filename for filename, _ in files}

                # Vérifier que tous les fichiers existent avant de charger quoi que ce soit
                missing = [str(p) for p in paths.values() if not p.exists()]
                if missing:
                    logger.warning(
                        "[RealMLEngine] Modèle '%s' ignoré — fichiers manquants : %s",
                        machine,
                        missing,
                    )
                    continue

                logger.debug("[RealMLEngine] Chargement XGBoost pour '%s'", machine)
                self.models[machine]         = joblib.load(paths[f"{machine}_xgb.pkl"])
                logger.debug("[RealMLEngine] Chargement scaler pour '%s'", machine)
                self.scalers[machine]        = joblib.load(paths[f"{machine}_scaler.pkl"])
                logger.debug("[RealMLEngine] Chargement label_encoder pour '%s'", machine)
                self.label_encoders[machine] = joblib.load(paths[f"{machine}_label_encoder.pkl"])
                logger.debug("[RealMLEngine] Chargement metadata pour '%s'", machine)

                with open(paths[f"{machine}_metadata.json"], encoding="utf-8") as fh:
                    self.metadata[machine] = json.load(fh)

                logger.info(
                    "[RealMLEngine] ✅ Modèle '%s' chargé — accuracy=%s",
                    machine,
                    self.metadata[machine].get("accuracy", "N/A"),
                )

            except Exception as exc:
                logger.error(
                    "[RealMLEngine] ❌ Échec du chargement du modèle '%s' : %s",
                    machine,
                    exc,
                    exc_info=True,
                )

        logger.info("[RealMLEngine] Modèles chargés: %s", list(self.models.keys()))
        
        if not self.models:
            raise RuntimeError(
                "[RealMLEngine] Aucun modèle n'a pu être chargé. "
                "Veuillez entraîner les modèles avant de démarrer le service."
            )

    # ------------------------------------------------------------------
    # Interface publique (identique à MockMLEngine)
    # ------------------------------------------------------------------

    def predict(self, machine: str, sensors: dict) -> dict:
        machine = (machine or "").lower()
        if machine not in self.models:
            raise ValueError(f"Modèle ML non entraîné pour '{machine}'. Entraînez d'abord le modèle.")
        try:
            features = self._extract_features(machine, sensors)
            return self._run_prediction(machine, features)
        except Exception as exc:
            logger.error("[RealMLEngine] Erreur prédiction '%s': %s", machine, exc)
            return self._fallback(machine)

    # ------------------------------------------------------------------
    # Extraction des features
    # ------------------------------------------------------------------

    def _extract_features(self, machine: str, sensors: dict) -> pd.DataFrame:
        """
        Construit le vecteur de 9 features depuis les données sensors.

        Le service IoT envoie des features pré-calculées sur une fenêtre :
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
        v = float(sensors.get("vibration", 0.0))
        c = float(sensors.get("current",   0.0))

        signal = np.array([
            v, -v * 0.3, v * 0.7, -v * 0.5, c / 20,
            v * 0.9, -v * 0.2, v * 0.6, -v * 0.4,
            v * 0.8, -v * 0.4, v * 0.5, -v * 0.3, v * 0.7,
        ])

        rms      = float(np.sqrt(np.mean(signal ** 2)))
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

        raw_label   = label_encoder.inverse_transform([predicted_idx])[0]
        defect_name = _map_class(raw_label)
        confidence  = float(proba[predicted_idx])

        # defect_score = 1 - P(any normal class)
        normal_indices = [
            i for i, cls in enumerate(label_encoder.classes_)
            if _map_class(cls) == "normal_operation"
        ]
        if normal_indices:
            normal_prob  = float(sum(proba[i] for i in normal_indices))
            defect_score = float(1.0 - normal_prob)
        else:
            defect_score = float(1.0 - proba[0])

        # Aggregate probabilities by SmartMaintain defect name
        defect_scores: dict[str, float] = {}
        for cls, p in zip(label_encoder.classes_, proba):
            mapped = _map_class(cls)
            defect_scores[mapped] = round(defect_scores.get(mapped, 0.0) + float(p), 4)

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
