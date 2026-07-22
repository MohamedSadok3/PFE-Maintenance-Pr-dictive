# SmartMaintain ML Model Training Guide

## Overview

This directory contains training notebooks and model artifacts for all 4 machine types in SmartMaintain.

## Machine Types & Models

| Machine | Notebook | Dataset | Defects | Status |
|---------|----------|---------|---------|--------|
| **moteur** | `train_model.py` (CLI) | CWRU Bearing | degradation_roulement, desequilibre_desalignement | ✅ Trained |
| **pompe** | `train_pompe_colab.ipynb` | Pump Sensor Data | cavitation, usure_garniture_mecanique | ⏳ Needs training |
| **compresseur** | `train_compresseur_colab.ipynb` | Compressor Data | usure_soupapes, refroidissement_huile | ⏳ Needs training |
| **echangeur** | `train_echangeur_colab.ipynb` | Synthetic (physics) | encrassement_progressif, fuite_interne | ⏳ Needs training |

## Quick Start

### Option 1: Use Existing Models (Synthetic Data)

The models are already trained with synthetic data and ready to use:

```bash
# Check that all model files exist
ls -la backend/ml/models/*.pkl backend/ml/models/*.json

# Restart ML service
docker-compose restart ml

# Verify models loaded
docker-compose exec ml python -c "from services.ml_service import MLService; svc = MLService(); print('Models loaded:', list(svc.engine.models.keys()))"
```

### Option 2: Train with Real Datasets (Recommended)

For production use, train models with real datasets using Google Colab.

## Training New Models

### Prerequisites

1. **Google Colab account** (free)
2. **Kaggle API token** for dataset downloads
   - Go to https://www.kaggle.com/settings
   - Click "Create New API Token"
   - Download `kaggle.json`

### Steps for Each Machine

#### 1. POMPE (Pump)

**Dataset**: [Pump Sensor Data](https://www.kaggle.com/datasets/nphantawee/pump-sensor-data)

```bash
# 1. Open notebook in Google Colab
# Upload: train_pompe_colab.ipynb

# 2. Run all cells (Runtime > Run all)
# 3. When prompted, upload kaggle.json
# 4. Download the 4 output files:
#    - pompe_xgb.pkl
#    - pompe_scaler.pkl
#    - pompe_label_encoder.pkl
#    - pompe_metadata.json

# 5. Copy to project
cp ~/Downloads/pompe_*.pkl backend/ml/models/
cp ~/Downloads/pompe_*.json backend/ml/models/

# 6. Restart service
docker-compose restart ml
```

**Expected accuracy**: 85-95%

#### 2. COMPRESSEUR (Compressor)

**Dataset**: [Compressor Data](https://www.kaggle.com/datasets/pythonkumar/compressor-data)

```bash
# Same steps as pompe, but use:
# - train_compresseur_colab.ipynb
# - Output files: compresseur_*.*
```

**Expected accuracy**: 85-95%

#### 3. ECHANGEUR (Heat Exchanger)

**Dataset**: Synthetic (physics-based simulation)

```bash
# No Kaggle API needed - synthetic data
# Upload: train_echangeur_colab.ipynb
# Run all cells
# Download: echangeur_*.*
```

**Expected accuracy**: 85-95%

## Model Architecture

### Feature Engineering

Each model extracts **9 statistical features** from sensor windows (20 samples):

```python
features = [
    'max',        # Maximum value
    'min',        # Minimum value
    'mean',       # Average value
    'sd',         # Standard deviation
    'rms',        # Root mean square
    'skewness',   # Distribution skewness
    'kurtosis',   # Distribution kurtosis
    'crest',      # Crest factor (peak / RMS)
    'form',       # Form factor (RMS / mean absolute)
]
```

For 3 sensors per machine → **27 features total**

### XGBoost Configuration

```python
XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    objective='multi:softprob',
    random_state=42,
)
```

### Training Pipeline

1. **Load data** (real or synthetic)
2. **Extract features** from time windows
3. **Split data** (80% train, 20% test) - BEFORE augmentation
4. **Encode labels** (LabelEncoder)
5. **Scale features** (StandardScaler)
6. **Train model** (XGBoost)
7. **Validate** (5-fold cross-validation)
8. **Save artifacts** (model + scaler + encoder + metadata)

## File Structure

```
backend/ml/models/
├── README_TRAINING.md              # This file
├── train_model.py                  # CLI training for all machines
├── train_pompe_colab.ipynb        # Colab: POMPE
├── train_compresseur_colab.ipynb  # Colab: COMPRESSEUR
├── train_echangeur_colab.ipynb    # Colab: ECHANGEUR
│
├── moteur_xgb.pkl                 # ✅ Model
├── moteur_scaler.pkl              # ✅ Scaler
├── moteur_label_encoder.pkl       # ✅ Encoder
├── moteur_metadata.json           # ✅ Metadata
│
├── pompe_xgb.pkl                  # Model
├── pompe_scaler.pkl               # Scaler
├── pompe_label_encoder.pkl        # Encoder
├── pompe_metadata.json            # Metadata
│
├── compresseur_xgb.pkl            # Model
├── compresseur_scaler.pkl         # Scaler
├── compresseur_label_encoder.pkl  # Encoder
├── compresseur_metadata.json      # Metadata
│
├── echangeur_xgb.pkl              # Model
├── echangeur_scaler.pkl           # Scaler
├── echangeur_label_encoder.pkl    # Encoder
└── echangeur_metadata.json        # Metadata
```

## Defect Classes

### Moteur (Motor)
- `normal_operation` - Healthy operation
- `degradation_roulement` - Bearing degradation
- `desequilibre_desalignement` - Imbalance/misalignment

### Pompe (Pump)
- `normal_operation` - Healthy operation
- `cavitation` - Cavitation bubbles
- `usure_garniture_mecanique` - Mechanical seal wear

### Compresseur (Compressor)
- `normal_operation` - Healthy operation
- `usure_soupapes` - Valve wear
- `refroidissement_huile` - Oil cooling issues

### Echangeur (Heat Exchanger)
- `normal_operation` - Healthy operation
- `encrassement_progressif` - Progressive fouling
- `fuite_interne` - Internal leak

## Testing Models

### Test via API

```bash
# Test moteur
curl -X POST http://localhost:5000/api/ml/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "machine": "moteur",
    "sensors": {
      "vibration": 1.5,
      "current": 14.2
    }
  }'

# Test pompe
curl -X POST http://localhost:5000/api/ml/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "machine": "pompe",
    "sensors": {
      "vibration": 0.8,
      "pressure_in": 4.5,
      "pressure_out": 8.2
    }
  }'
```

### Test in Docker

```bash
docker-compose exec ml python -c "
from engines.real_engine import RealMLEngine
import numpy as np

engine = RealMLEngine()

# Test moteur
result = engine.predict('moteur', {'vibration': 1.5, 'current': 14.2})
print('Moteur:', result['defect'], f\"({result['confidence']:.2%})\")

# Test pompe
result = engine.predict('pompe', {'vibration': 0.8, 'pressure_in': 4.5, 'pressure_out': 8.2})
print('Pompe:', result['defect'], f\"({result['confidence']:.2%})\")
"
```

## Troubleshooting

### Models not loading

```bash
# Check files exist
docker-compose exec ml ls -la /app/models/

# Check logs
docker-compose logs ml | grep -i "error\|warning"

# Verify MOCK_ML is false
docker-compose exec ml env | grep MOCK_ML
```

### Low accuracy

- **Check class balance** - ensure equal samples per class
- **Increase training data** - aim for 500+ samples per class
- **Tune hyperparameters** - adjust max_depth, learning_rate
- **Add more features** - time-domain, frequency-domain

### Dataset not found

- Verify Kaggle API token is correct
- Check dataset URL is still available
- Try downloading manually from Kaggle

## Model Retraining

To retrain a model with new data:

```bash
# 1. Update training notebook with new data
# 2. Run notebook in Colab
# 3. Download new model files
# 4. Replace old files in backend/ml/models/
# 5. Restart service
docker-compose restart ml

# 6. Test predictions to verify
```

## Performance Benchmarks

| Machine | Accuracy | Precision | Recall | F1-Score |
|---------|----------|-----------|--------|----------|
| moteur | 100% | 1.00 | 1.00 | 1.00 |
| pompe | Target: 90% | Target: 0.88+ | Target: 0.87+ | Target: 0.88+ |
| compresseur | Target: 90% | Target: 0.88+ | Target: 0.87+ | Target: 0.88+ |
| echangeur | Target: 90% | Target: 0.88+ | Target: 0.87+ | Target: 0.88+ |

## References

- **CWRU Bearing Dataset**: https://engineering.case.edu/bearingdatacenter
- **Pump Sensor Data**: https://www.kaggle.com/datasets/nphantawee/pump-sensor-data
- **Compressor Data**: https://www.kaggle.com/datasets/pythonkumar/compressor-data
- **XGBoost Documentation**: https://xgboost.readthedocs.io/
- **Scikit-learn**: https://scikit-learn.org/

## Support

For issues or questions:
1. Check model logs: `docker-compose logs ml`
2. Verify file permissions: `ls -la backend/ml/models/`
3. Test model loading: `docker-compose exec ml python -c "from services.ml_service import MLService; MLService()"`

---

**Last updated**: 2026-07-18  
**Maintainer**: SmartMaintain ML Team
