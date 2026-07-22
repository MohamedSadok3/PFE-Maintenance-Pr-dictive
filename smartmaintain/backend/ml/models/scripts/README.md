# Training & Testing Scripts

Python scripts for training and testing models locally or in Docker.

## 📜 Available Scripts

### 1. train_model.py
**Purpose**: Train ML models for all machines or specific machine  
**Environment**: Docker container or local Python  
**Datasets**: Synthetic data generation (CWRU for moteur if available)

#### Usage

```bash
# Train all machines
docker-compose exec ml python /app/models/scripts/train_model.py

# Train specific machine
docker-compose exec ml python /app/models/scripts/train_model.py --machine moteur
docker-compose exec ml python /app/models/scripts/train_model.py --machine pompe
docker-compose exec ml python /app/models/scripts/train_model.py --machine compresseur
docker-compose exec ml python /app/models/scripts/train_model.py --machine echangeur
```

#### Options

```
--machine {all,moteur,pompe,compresseur,echangeur}
    Machine type to train (default: all)
```

#### Output

```
Trained models saved to: /app/models/trained/
- {machine}_xgb.pkl
- {machine}_scaler.pkl
- {machine}_label_encoder.pkl
- {machine}_metadata.json
```

#### Features

- ✅ Automatic synthetic data generation
- ✅ CWRU dataset loading (if available for moteur)
- ✅ 9 statistical features per sensor
- ✅ 5-fold cross-validation
- ✅ Model metadata export

---

### 2. test_model.py
**Purpose**: Test trained models locally (simulates IoT payload)  
**Environment**: Docker container with trained models loaded

#### Usage

```bash
# Test moteur model
docker-compose exec ml python /app/models/scripts/test_model.py
```

#### What it tests

1. **Model loading** - Verifies all 4 files can be loaded
2. **Feature extraction** - Tests 9 statistical features
3. **Label mapping** - CWRU → SmartMaintain defect names
4. **Prediction** - 4 test scenarios per machine:
   - Normal operation
   - Defect 1 (high severity)
   - Defect 2 (medium severity)
   - Borderline case

#### Output

```
==================================================
  SIMULATION DES PAYLOADS IoT — SmartMaintain
==================================================

🟢 Moteur normal (vibration faible)
--------------------------------------------------
  📡 Payload reçu : machine=moteur, sensors={'vibration': 0.15, 'current': 11.5}
  ✅ Défaut détecté  : normal_operation
  📊 Defect Score    : 0.0234
  🎯 Confidence      : 0.9654
  🏷️  Label CWRU brut : normal
  📋 Defect Scores   :
     normal_operation                    : 0.9654 ████████████████████
     degradation_roulement               : 0.0234 ██
     desequilibre_desalignement          : 0.0112 █
```

---

## 🔧 Script Details

### train_model.py

#### Dependencies

```python
import numpy as np
import pandas as pd
import joblib
from scipy.stats import skew, kurtosis
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier
```

#### Data Generation

**MOTEUR**: Tries CWRU dataset, falls back to synthetic
```python
# Look for: /Datasets Pfe/Datasets Mouteur electrique/CWRU_48k_load_1_CNN_data.npz
```

**POMPE, COMPRESSEUR, ECHANGEUR**: Physics-based synthetic
```python
def generate_synthetic_data(machine: str, n_samples: int = 2000):
    # Simulates realistic sensor patterns
    # - Normal: baseline values + small noise
    # - Defect 1: characteristic pattern 1
    # - Defect 2: characteristic pattern 2
```

#### Feature Extraction

```python
def extract_features(signal: np.ndarray) -> np.ndarray:
    """
    Extract 9 statistical features:
    1. max          - Maximum value
    2. min          - Minimum value
    3. mean         - Average value
    4. sd           - Standard deviation
    5. rms          - Root mean square
    6. skewness     - Distribution asymmetry
    7. kurtosis     - Distribution tailedness
    8. crest        - Peak / RMS ratio
    9. form         - RMS / mean absolute ratio
    """
```

#### Training Pipeline

1. Generate or load data
2. Extract features from windows
3. Split train/test (80/20)
4. Encode labels
5. Scale features
6. Train XGBoost
7. 5-fold cross-validation
8. Save artifacts

---

### test_model.py

#### Test Scenarios

```python
test_cases = [
    {
        "description": "🟢 Moteur normal (vibration faible)",
        "payload": {"machine": "moteur", "sensors": {"vibration": 0.15, "current": 11.5}}
    },
    {
        "description": "🔴 Dégradation roulement (vibration élevée)",
        "payload": {"machine": "moteur", "sensors": {"vibration": 1.8, "current": 12.0}}
    },
    {
        "description": "🟠 Déséquilibre (vibration + current élevés)",
        "payload": {"machine": "moteur", "sensors": {"vibration": 1.2, "current": 19.5}}
    },
    {
        "description": "🟡 Zone limite (valeurs moyennes)",
        "payload": {"machine": "moteur", "sensors": {"vibration": 0.6, "current": 14.0}}
    },
]
```

#### Validation Checks

- ✅ Model files exist
- ✅ Models load successfully
- ✅ Feature extraction works
- ✅ Predictions are valid
- ✅ Confidence scores in [0, 1]
- ✅ Defect scores sum to ~1.0

---

## 🚀 Quick Commands

### Train All Models (Synthetic)
```bash
docker-compose exec ml python /app/models/scripts/train_model.py
```

### Test All Models
```bash
docker-compose exec ml python /app/models/scripts/test_model.py
```

### Train One Machine
```bash
docker-compose exec ml python /app/models/scripts/train_model.py --machine pompe
```

### Verify Models Loaded in Service
```bash
docker-compose exec ml python -c "
from services.ml_service import MLService
svc = MLService()
print('Models:', list(svc.engine.models.keys()))
"
```

---

## 🐛 Troubleshooting

### Script not found
```bash
# Verify scripts directory mounted
docker-compose exec ml ls -la /app/models/scripts/
```

### Import errors
```bash
# Check dependencies installed
docker-compose exec ml pip list | grep -E "xgboost|scikit-learn|joblib"
```

### CWRU dataset not found (moteur)
```
[WARNING] CWRU dataset not found at /Datasets Pfe/...
[INFO] CWRU data not available, generating synthetic data for moteur
```
**This is normal** - script falls back to synthetic data.

To use real CWRU data:
```bash
# Download CWRU dataset
# Place in: Datasets Pfe/Datasets Mouteur electrique/CWRU_48k_load_1_CNN_data.npz
```

### Training fails with OOM
```bash
# Reduce sample size
docker-compose exec ml python /app/models/scripts/train_model.py

# Edit train_model.py:
# n_samples=2000  →  n_samples=1000
```

---

## 📊 Performance Benchmarks

| Script | Execution Time | Output |
|--------|---------------|---------|
| train_model.py --machine all | ~60 seconds | 16 files |
| train_model.py --machine moteur | ~15 seconds | 4 files |
| test_model.py | ~5 seconds | Console output |

**System**: Docker container, 4 CPU cores, 8GB RAM

---

## 🔗 Related Files

- **Training notebooks**: `../notebooks/` (Google Colab alternatives)
- **Trained models**: `../trained/` (output directory)
- **Engine code**: `../../engines/real_engine.py` (loads models)
- **Service code**: `../../services/ml_service.py` (uses models)

---

## 📝 Notes

- Scripts use **synthetic data** by default
- For **real datasets**, use **Google Colab notebooks** instead
- Scripts are for **quick prototyping** and **CI/CD pipelines**
- Production models should be trained with **real sensor data**

---

**Maintained by**: SmartMaintain ML Team  
**Last Updated**: 2026-07-18
