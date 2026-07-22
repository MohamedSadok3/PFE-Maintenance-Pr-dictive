"""
Train XGBoost models for SmartMaintain
=======================================
Trains models for all machine types (moteur, pompe, compresseur, echangeur).

For 'moteur': Uses CWRU bearing dataset if available
For others: Generates synthetic training data based on sensor characteristics

Outputs for each machine:
  - {machine}_xgb.pkl          : Trained XGBoost model
  - {machine}_scaler.pkl       : StandardScaler for feature normalization
  - {machine}_label_encoder.pkl: LabelEncoder for class labels
  - {machine}_metadata.json    : Model metadata (accuracy, classes, etc.)

Usage:
    python backend/ml/models/train_model.py
    python backend/ml/models/train_model.py --machine moteur
    python backend/ml/models/train_model.py --machine all
"""

import argparse
import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy.stats import kurtosis, skew
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent
OUTPUT_DIR = MODELS_DIR

# Defect classes per machine type
DEFECT_CLASSES = {
    "moteur": ["normal_operation", "degradation_roulement", "desequilibre_desalignement"],
    "pompe": ["normal_operation", "cavitation", "fuite_joints"],
    "compresseur": ["normal_operation", "surchauffe", "fuite_air"],
    "echangeur": ["normal_operation", "encrassement", "fuite_thermique"],
}

# Feature names (9 statistical features from vibration/sensor data)
FEATURE_NAMES = ["max", "min", "mean", "sd", "rms", "skewness", "kurtosis", "crest", "form"]


def extract_features(signal: np.ndarray) -> np.ndarray:
    """Extract 9 statistical features from a signal."""
    signal = np.asarray(signal)
    rms = np.sqrt(np.mean(signal ** 2))
    mean_abs = np.mean(np.abs(signal))
    
    return np.array([
        np.max(signal),
        np.min(signal),
        np.mean(signal),
        np.std(signal),
        rms,
        skew(signal),
        kurtosis(signal),
        np.max(np.abs(signal)) / (rms + 1e-10),  # crest factor
        rms / (mean_abs + 1e-10),  # form factor
    ])


def load_cwru_data() -> tuple[pd.DataFrame, np.ndarray]:
    """
    Load CWRU bearing dataset if available.
    
    Expected location: Datasets Pfe/Datasets Mouteur electrique/CWRU_48k_load_1_CNN_data.npz
    
    Returns:
        (features_df, labels_array)
    """
    project_root = MODELS_DIR.parent.parent.parent.parent
    cwru_path = project_root / "Datasets Pfe" / "Datasets Mouteur electrique" / "CWRU_48k_load_1_CNN_data.npz"
    
    if not cwru_path.exists():
        logger.warning(f"CWRU dataset not found at {cwru_path}")
        return None, None
    
    try:
        data = np.load(cwru_path, allow_pickle=True)
        X = data['data']  # shape: (n_samples, window_size)
        y = data['labels']  # shape: (n_samples,)
        
        logger.info(f"Loaded CWRU dataset: {X.shape[0]} samples, {X.shape[1]} points per window")
        
        # Extract features from each window
        features = np.array([extract_features(window) for window in X])
        features_df = pd.DataFrame(features, columns=FEATURE_NAMES)
        
        # Map CWRU labels to SmartMaintain defect classes
        cwru_to_sm = {
            "Normal_1": "normal_operation",
            "Ball_007_1": "degradation_roulement",
            "Ball_014_1": "degradation_roulement",
            "Ball_021_1": "degradation_roulement",
            "IR_007_1": "degradation_roulement",
            "IR_014_1": "degradation_roulement",
            "IR_021_1": "degradation_roulement",
            "OR_007_6_1": "desequilibre_desalignement",
            "OR_014_6_1": "desequilibre_desalignement",
            "OR_021_6_1": "desequilibre_desalignement",
        }
        
        # Convert numeric labels to string if needed
        if y.dtype.kind in ['i', 'u', 'f']:
            # Assume labels are: 0=Normal, 1-3=Ball, 4-6=IR, 7-9=OR
            label_map = {
                0: "Normal_1",
                1: "Ball_007_1", 2: "Ball_014_1", 3: "Ball_021_1",
                4: "IR_007_1", 5: "IR_014_1", 6: "IR_021_1",
                7: "OR_007_6_1", 8: "OR_014_6_1", 9: "OR_021_6_1",
            }
            y = np.array([label_map.get(int(label), "normal_operation") for label in y])
        
        # Map to SmartMaintain labels
        y_mapped = np.array([cwru_to_sm.get(str(label), "normal_operation") for label in y])
        
        logger.info(f"Feature extraction complete: {features_df.shape}")
        logger.info(f"Class distribution: {dict(zip(*np.unique(y_mapped, return_counts=True)))}")
        
        return features_df, y_mapped
        
    except Exception as e:
        logger.error(f"Failed to load CWRU dataset: {e}")
        return None, None


def generate_synthetic_data(machine: str, n_samples: int = 2000) -> tuple[pd.DataFrame, np.ndarray]:
    """
    Generate synthetic training data for machines without real datasets.
    
    Args:
        machine: Machine type (pompe, compresseur, echangeur)
        n_samples: Total number of samples to generate
    
    Returns:
        (features_df, labels_array)
    """
    logger.info(f"Generating {n_samples} synthetic samples for {machine}")
    
    classes = DEFECT_CLASSES[machine]
    samples_per_class = n_samples // len(classes)
    
    all_features = []
    all_labels = []
    
    # Define characteristic patterns for each defect class
    defect_patterns = {
        "normal_operation": {
            "vibration_range": (0.1, 0.4),
            "noise_std": 0.05,
            "frequency_boost": 1.0,
        },
        # Bearing defects (high vibration, high kurtosis)
        "degradation_roulement": {
            "vibration_range": (1.0, 2.5),
            "noise_std": 0.3,
            "frequency_boost": 3.0,
        },
        "desequilibre_desalignement": {
            "vibration_range": (0.8, 1.8),
            "noise_std": 0.2,
            "frequency_boost": 2.0,
        },
        # Pump defects
        "cavitation": {
            "vibration_range": (0.6, 1.4),
            "noise_std": 0.4,
            "frequency_boost": 2.5,
        },
        "fuite_joints": {
            "vibration_range": (0.3, 0.8),
            "noise_std": 0.15,
            "frequency_boost": 1.2,
        },
        # Compressor defects
        "surchauffe": {
            "vibration_range": (0.5, 1.2),
            "noise_std": 0.25,
            "frequency_boost": 1.8,
        },
        "fuite_air": {
            "vibration_range": (0.4, 0.9),
            "noise_std": 0.2,
            "frequency_boost": 1.5,
        },
        # Heat exchanger defects
        "encrassement": {
            "vibration_range": (0.3, 0.7),
            "noise_std": 0.1,
            "frequency_boost": 1.3,
        },
        "fuite_thermique": {
            "vibration_range": (0.2, 0.6),
            "noise_std": 0.12,
            "frequency_boost": 1.1,
        },
    }
    
    for defect_class in classes:
        pattern = defect_patterns[defect_class]
        
        for _ in range(samples_per_class):
            # Generate synthetic signal (simulated vibration window)
            base_amplitude = np.random.uniform(*pattern["vibration_range"])
            signal_length = 1024
            
            # Create signal with characteristic frequency components
            t = np.linspace(0, 1, signal_length)
            signal = (
                base_amplitude * np.sin(2 * np.pi * 60 * t * pattern["frequency_boost"])
                + base_amplitude * 0.3 * np.sin(2 * np.pi * 120 * t)
                + np.random.normal(0, pattern["noise_std"], signal_length)
            )
            
            # Add impulses for bearing faults
            if "roulement" in defect_class or "cavitation" in defect_class:
                num_impulses = np.random.randint(3, 8)
                impulse_positions = np.random.choice(signal_length, num_impulses, replace=False)
                signal[impulse_positions] += np.random.uniform(1.5, 3.0, num_impulses) * base_amplitude
            
            # Extract features
            features = extract_features(signal)
            all_features.append(features)
            all_labels.append(defect_class)
    
    features_df = pd.DataFrame(all_features, columns=FEATURE_NAMES)
    labels_array = np.array(all_labels)
    
    logger.info(f"Synthetic data generated: {features_df.shape}")
    logger.info(f"Class distribution: {dict(zip(*np.unique(labels_array, return_counts=True)))}")
    
    return features_df, labels_array


def train_machine_model(machine: str) -> None:
    """
    Train and save model for a specific machine.
    
    Args:
        machine: Machine type (moteur, pompe, compresseur, echangeur)
    """
    logger.info(f"=" * 60)
    logger.info(f"Training model for: {machine}")
    logger.info(f"=" * 60)
    
    # Load or generate data
    if machine == "moteur":
        X, y = load_cwru_data()
        if X is None:
            logger.info("CWRU data not available, generating synthetic data for moteur")
            X, y = generate_synthetic_data(machine)
    else:
        X, y = generate_synthetic_data(machine)
    
    # Prepare data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_train_encoded = label_encoder.fit_transform(y_train)
    y_test_encoded = label_encoder.transform(y_test)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train XGBoost model
    logger.info("Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        objective='multi:softprob',
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train_encoded)
    
    # Evaluate
    train_accuracy = model.score(X_train_scaled, y_train_encoded)
    test_accuracy = model.score(X_test_scaled, y_test_encoded)
    
    logger.info(f"Training accuracy: {train_accuracy:.4f}")
    logger.info(f"Test accuracy: {test_accuracy:.4f}")
    
    # Save model artifacts
    model_prefix = OUTPUT_DIR / machine
    joblib.dump(model, f"{model_prefix}_xgb.pkl")
    joblib.dump(scaler, f"{model_prefix}_scaler.pkl")
    joblib.dump(label_encoder, f"{model_prefix}_label_encoder.pkl")
    
    # Save metadata
    metadata = {
        "model_name": f"XGBoost-{machine}-v1",
        "machine_type": machine,
        "accuracy": float(test_accuracy),
        "train_accuracy": float(train_accuracy),
        "classes": label_encoder.classes_.tolist(),
        "n_features": X.shape[1],
        "feature_names": FEATURE_NAMES,
        "n_samples_train": len(X_train),
        "n_samples_test": len(X_test),
    }
    
    with open(f"{model_prefix}_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"✅ Model saved to {OUTPUT_DIR}")
    logger.info(f"   - {machine}_xgb.pkl")
    logger.info(f"   - {machine}_scaler.pkl")
    logger.info(f"   - {machine}_label_encoder.pkl")
    logger.info(f"   - {machine}_metadata.json")
    logger.info("")


def main():
    parser = argparse.ArgumentParser(description="Train ML models for SmartMaintain")
    parser.add_argument(
        "--machine",
        type=str,
        default="all",
        choices=["all", "moteur", "pompe", "compresseur", "echangeur"],
        help="Machine type to train (default: all)",
    )
    args = parser.parse_args()
    
    machines = ["moteur", "pompe", "compresseur", "echangeur"] if args.machine == "all" else [args.machine]
    
    logger.info("SmartMaintain ML Training Pipeline")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Machines to train: {machines}")
    logger.info("")
    
    for machine in machines:
        try:
            train_machine_model(machine)
        except Exception as e:
            logger.error(f"Failed to train model for {machine}: {e}")
            continue
    
    logger.info("=" * 60)
    logger.info("✅ Training complete!")
    logger.info("=" * 60)
    logger.info("Next steps:")
    logger.info("  1. Restart ML service to load new models")
    logger.info("  2. Verify MOCK_ML=false in environment")
    logger.info("  3. Test predictions via /api/ml/predict")


if __name__ == "__main__":
    main()
