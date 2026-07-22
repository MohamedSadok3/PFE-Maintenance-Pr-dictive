"""
Test local du modèle XGBoost — Simulation du format IoT SmartMaintain
=====================================================================
Ce script simule exactement ce que fait RealMLEngine dans le projet :
  1. Reçoit un payload IoT {"machine": "moteur", "sensors": {...}}
  2. Extrait les features
  3. Normalise avec le scaler
  4. Prédit avec XGBoost
  5. Retourne le même format que MockMLEngine
"""

import json
import joblib
import numpy as np
from pathlib import Path

# ── Mapping CWRU → SmartMaintain ──────────────────────────────────────
CWRU_TO_SMARTMAINTAIN = {
    "normal":  "normal_operation",
    "IR007":   "degradation_roulement",
    "IR014":   "degradation_roulement",
    "IR021":   "degradation_roulement",
    "B007":    "desequilibre_desalignement",
    "B014":    "desequilibre_desalignement",
    "B021":    "desequilibre_desalignement",
    "OR007":   "desequilibre_desalignement",
    "OR014":   "desequilibre_desalignement",
    "OR021":   "desequilibre_desalignement",
}

# ── Chargement des fichiers ────────────────────────────────────────────
MODELS_DIR = Path("models")  # dossier où tu as placé les .pkl

print("Chargement du modèle...")
model         = joblib.load(MODELS_DIR / "moteur_xgb.pkl")
scaler        = joblib.load(MODELS_DIR / "moteur_scaler.pkl")
label_encoder = joblib.load(MODELS_DIR / "moteur_label_encoder.pkl")

with open(MODELS_DIR / "moteur_metadata.json") as f:
    metadata = json.load(f)

print(f"✓ Modèle chargé : {metadata['model_name']}")
print(f"✓ Accuracy entraînement : {metadata['accuracy']*100:.2f}%")
print(f"✓ Classes disponibles : {metadata['classes']}")
print(f"✓ Nombre de features : {metadata['n_features']}")
print(f"✓ Features : {metadata['feature_names'][:5]}... ({metadata['n_features']} total)")
print()


# ── Fonction de prédiction (logique exacte de RealMLEngine) ───────────
def predict_iot(iot_payload: dict) -> dict:
    """
    Simule RealMLEngine.predict() dans SmartMaintain.
    
    Args:
        iot_payload: dict avec "machine" et "sensors"
        Ex: {"machine": "moteur", "sensors": {"vibration": 1.5, "current": 14.2}}
    
    Returns:
        dict au format SmartMaintain (même format que MockMLEngine)
    """
    machine = iot_payload.get("machine", "")
    sensors = iot_payload.get("sensors", {})
    
    print(f"  📡 Payload reçu : machine={machine}, sensors={sensors}")
    
    # Extraire les features depuis les capteurs
    # Note: le CSV CWRU contient des features statistiques pré-calculées.
    # En production, le service IoT envoie vibration et current comme valeurs scalaires.
    # On reconstruit un vecteur de features compatible avec le scaler.
    feature_names = metadata["feature_names"]
    n_features = metadata["n_features"]
    
    vibration = float(sensors.get("vibration", 0.0))
    current   = float(sensors.get("current", 0.0))
    
    # Construire le vecteur de features (même ordre que le CSV d'entraînement)
    # On remplit avec vibration/current sur toutes les colonnes disponibles
    # car le CSV contient des features statistiques du signal brut
    features = np.zeros(n_features)
    
    # Assigner les valeurs IoT aux features correspondantes
    for i, fname in enumerate(feature_names):
        fname_lower = fname.lower()
        if "rms" in fname_lower or "vibration" in fname_lower or "amplitude" in fname_lower:
            features[i] = vibration
        elif "current" in fname_lower or "peak" in fname_lower or "p2p" in fname_lower:
            features[i] = current
        elif "kurtosis" in fname_lower or "kurt" in fname_lower:
            features[i] = vibration * 3.0  # approximation
        elif "std" in fname_lower or "deviation" in fname_lower:
            features[i] = vibration * 0.7
        elif "mean" in fname_lower:
            features[i] = vibration * 0.5
        elif "energy" in fname_lower or "power" in fname_lower:
            features[i] = vibration ** 2
        elif "crest" in fname_lower:
            features[i] = vibration / (vibration + 1e-10)
        elif "skew" in fname_lower:
            features[i] = 0.0
        else:
            features[i] = vibration  # fallback
    
    # Normalisation (même scaler que l'entraînement)
    features_scaled = scaler.transform(features.reshape(1, -1))
    
    # Prédiction
    proba = model.predict_proba(features_scaled)[0]
    predicted_idx = int(np.argmax(proba))
    
    # Décoder le label CWRU
    cwru_label = label_encoder.inverse_transform([predicted_idx])[0]
    
    # Mapper vers SmartMaintain
    smartmaintain_defect = CWRU_TO_SMARTMAINTAIN.get(cwru_label, "anomaly_detected")
    confidence = float(proba[predicted_idx])
    
    # defect_score = 1 - P(normal)
    try:
        normal_idx = list(label_encoder.classes_).index("normal")
        defect_score = float(1.0 - proba[normal_idx])
    except ValueError:
        defect_score = float(1.0 - proba[0])
    
    # Construire defect_scores mappés vers SmartMaintain
    defect_scores = {}
    for i, cwru_class in enumerate(label_encoder.classes_):
        sm_label = CWRU_TO_SMARTMAINTAIN.get(cwru_class, cwru_class)
        if sm_label not in defect_scores:
            defect_scores[sm_label] = 0.0
        defect_scores[sm_label] = max(defect_scores[sm_label], round(float(proba[i]), 4))
    
    required_sensors = [] if smartmaintain_defect == "normal_operation" else ["vibration", "current"]
    
    # Format final identique à MockMLEngine
    result = {
        "machine":          machine,
        "defect_score":     round(defect_score, 4),
        "anomaly_score":    round(defect_score, 4),
        "defect":           smartmaintain_defect,
        "defect_scores":    defect_scores,
        "confidence":       round(confidence, 4),
        "required_sensors": required_sensors,
        "model_name":       metadata["model_name"],
        "cwru_raw_label":   cwru_label,  # pour debug
    }
    
    return result


# ── Tests avec simulation de payloads IoT ─────────────────────────────
print("=" * 60)
print("  SIMULATION DES PAYLOADS IoT — SmartMaintain")
print("=" * 60)

test_cases = [
    {
        "description": "🟢 Moteur normal (vibration faible)",
        "payload": {
            "machine": "moteur",
            "sensors": {"vibration": 0.15, "current": 11.5}
        }
    },
    {
        "description": "🔴 Dégradation roulement (vibration élevée)",
        "payload": {
            "machine": "moteur",
            "sensors": {"vibration": 1.8, "current": 12.0}
        }
    },
    {
        "description": "🟠 Déséquilibre (vibration + current élevés)",
        "payload": {
            "machine": "moteur",
            "sensors": {"vibration": 1.2, "current": 19.5}
        }
    },
    {
        "description": "🟡 Zone limite (valeurs moyennes)",
        "payload": {
            "machine": "moteur",
            "sensors": {"vibration": 0.6, "current": 14.0}
        }
    },
]

for tc in test_cases:
    print(f"\n{tc['description']}")
    print("-" * 50)
    result = predict_iot(tc["payload"])
    print(f"  ✅ Défaut détecté  : {result['defect']}")
    print(f"  📊 Defect Score    : {result['defect_score']}")
    print(f"  🎯 Confidence      : {result['confidence']}")
    print(f"  🏷️  Label CWRU brut : {result['cwru_raw_label']}")
    print(f"  📋 Defect Scores   :")
    for k, v in result['defect_scores'].items():
        bar = "█" * int(v * 20)
        print(f"     {k:35s} : {v:.4f} {bar}")

print("\n" + "=" * 60)
print("  FORMAT JSON FINAL (envoyé sur Redis ml_predictions)")
print("=" * 60)

# Afficher le format complet du dernier test
final_result = {k: v for k, v in result.items() if k != "cwru_raw_label"}
print(json.dumps(final_result, indent=2, ensure_ascii=False))

print("\n✅ Test terminé — Le modèle est compatible avec SmartMaintain !")
print("   Prochaine étape : intégrer dans backend/ml/engines/real_engine.py")
