# SmartMaintain ML Models

Trained machine learning models for predictive maintenance across 4 machine types.

## 📁 Directory Structure

```
models/
├── README.md                    # This file
├── README_TRAINING.md          # Detailed training guide
│
├── trained/                    # ✅ Trained model artifacts (loaded by RealMLEngine)
│   ├── moteur_xgb.pkl
│   ├── moteur_scaler.pkl
│   ├── moteur_label_encoder.pkl
│   ├── moteur_metadata.json
│   ├── pompe_xgb.pkl
│   ├── pompe_scaler.pkl
│   ├── pompe_label_encoder.pkl
│   ├── pompe_metadata.json
│   ├── compresseur_xgb.pkl
│   ├── compresseur_scaler.pkl
│   ├── compresseur_label_encoder.pkl
│   ├── compresseur_metadata.json
│   ├── echangeur_xgb.pkl
│   ├── echangeur_scaler.pkl
│   ├── echangeur_label_encoder.pkl
│   └── echangeur_metadata.json
│
├── notebooks/                  # 📓 Google Colab training notebooks
│   ├── train_pompe_colab.ipynb
│   ├── train_compresseur_colab.ipynb
│   └── train_echangeur_colab.ipynb
│
└── scripts/                    # 🔧 Training and testing scripts
    ├── train_model.py          # CLI trainer for all machines
    └── test_model.py           # Local model testing script
```

## 🎯 Quick Reference

### Machine Types

| Machine | Defects | Sensors | Accuracy |
|---------|---------|---------|----------|
| **moteur** | degradation_roulement, desequilibre_desalignement | vibration, current | 100% |
| **pompe** | cavitation, usure_garniture_mecanique | vibration, pressure_in, pressure_out | 100% |
| **compresseur** | usure_soupapes, refroidissement_huile | pressure, current, temperature_oil | 96.5% |
| **echangeur** | encrassement_progressif, fuite_interne | temp_in_hot, temp_out_hot, flow_rate | 92.5% |

All machines also detect `normal_operation` state.

### Model Architecture

- **Algorithm**: XGBoost (100 trees, max_depth=6)
- **Features**: 9 statistical features per sensor (27 total)
- **Input**: Time window of 20 samples
- **Output**: Defect class + confidence scores

## 🚀 Using Trained Models

### Check Models Loaded

```bash
docker-compose exec ml python -c "
from services.ml_service import MLService
svc = MLService()
print('Mock mode:', svc.mock_ml)  # Should be False
print('Models loaded:', list(svc.engine.models.keys()))
"
```

### Test Prediction

```bash
docker-compose exec ml python -c "
from engines.real_engine import RealMLEngine
engine = RealMLEngine()
result = engine.predict('moteur', {'vibration': 1.5, 'current': 14.2})
print(f'{result[\"defect\"]} (confidence: {result[\"confidence\"]:.0%})')
"
```

### Via API

```bash
curl -X POST http://localhost:5000/api/ml/predict \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "machine": "moteur",
    "sensors": {"vibration": 1.5, "current": 14.2}
  }'
```

## 📝 Training New Models

### Option 1: Google Colab (Recommended)

1. **Upload notebook** from `notebooks/` to [Google Colab](https://colab.research.google.com/)
2. **Get Kaggle API token** from https://www.kaggle.com/settings
3. **Run all cells** in the notebook
4. **Download 4 files** per machine:
   - `{machine}_xgb.pkl`
   - `{machine}_scaler.pkl`
   - `{machine}_label_encoder.pkl`
   - `{machine}_metadata.json`
5. **Copy to `trained/`** directory
6. **Restart service**: `docker-compose restart ml`

### Option 2: CLI Script (Docker)

```bash
# Train all machines (synthetic data)
docker-compose exec ml python /app/models/scripts/train_model.py

# Train specific machine
docker-compose exec ml python /app/models/scripts/train_model.py --machine pompe
```

## 📊 Model Files

### Required Files per Machine (4 total)

1. **`{machine}_xgb.pkl`** - Trained XGBoost classifier
2. **`{machine}_scaler.pkl`** - StandardScaler for feature normalization
3. **`{machine}_label_encoder.pkl`** - LabelEncoder for class mapping
4. **`{machine}_metadata.json`** - Model metrics and configuration

### Metadata Schema

```json
{
  "model_name": "XGBoost-moteur-v1",
  "machine_type": "moteur",
  "accuracy": 1.0,
  "train_accuracy": 1.0,
  "classes": ["degradation_roulement", "desequilibre_desalignement", "normal_operation"],
  "n_features": 9,
  "feature_names": ["max", "min", "mean", "sd", "rms", "skewness", "kurtosis", "crest", "form"],
  "n_samples_train": 1598,
  "n_samples_test": 400
}
```

## 🔧 Maintenance

### Adding a New Machine Type

1. **Create training notebook** in `notebooks/`
2. **Train model** with appropriate sensors
3. **Save 4 artifacts** to `trained/`
4. **Update RealMLEngine**:
   - Add to `_REQUIRED_FILES` dict
   - Add to `REQUIRED_SENSORS_MAP`
5. **Restart service**

### Updating Existing Model

1. **Train new version** (use notebooks or scripts)
2. **Backup old files**:
   ```bash
   cp trained/moteur_*.pkl trained/backup/
   ```
3. **Replace with new files**
4. **Update version** in metadata.json
5. **Restart service**
6. **Verify predictions**

### Troubleshooting

#### Models not loading

```bash
# Check files exist
docker-compose exec ml ls -la /app/models/trained/

# Should see 16 files (4 × 4 machines)
```

#### Prediction errors

```bash
# Check logs
docker-compose logs ml --tail=100 | grep -i error

# Test individual model
docker-compose exec ml python /app/models/scripts/test_model.py
```

#### Mock mode still active

```bash
# Check environment
docker-compose exec ml env | grep MOCK_ML
# Should output: MOCK_ML=false

# If not, update .env and restart
docker-compose restart ml
```

## 📚 Documentation

- **Training Guide**: `README_TRAINING.md` - Complete training documentation
- **Quick Start**: `../../ML_TRAINING_SUMMARY.md` - Executive summary
- **API Docs**: `../routes/predict.py` - Prediction endpoint

## 🔗 Resources

### Datasets
- **CWRU Bearing**: https://engineering.case.edu/bearingdatacenter
- **Pump Sensors**: https://www.kaggle.com/datasets/nphantawee/pump-sensor-data
- **Compressor**: https://www.kaggle.com/datasets/pythonkumar/compressor-data

### Libraries
- **XGBoost**: https://xgboost.readthedocs.io/
- **Scikit-learn**: https://scikit-learn.org/
- **Joblib**: https://joblib.readthedocs.io/

## ⚙️ Configuration

### Environment Variables

```bash
# Enable real models (not mock)
MOCK_ML=false

# Model directory (inside container)
ML_MODELS_PATH=/app/models/trained
```

### Docker Volume

```yaml
ml:
  volumes:
    - ./backend/ml/models/trained:/app/models/trained
```

## 📊 Performance Benchmarks

| Machine | Train Acc | Test Acc | CV Mean | CV Std |
|---------|-----------|----------|---------|--------|
| moteur | 100% | 100% | 0.99 | 0.01 |
| pompe | 100% | 100% | 0.99 | 0.01 |
| compresseur | 100% | 96.5% | 0.95 | 0.03 |
| echangeur | 99.4% | 92.5% | 0.91 | 0.04 |

> **Note**: 100% accuracy on synthetic data. Real datasets should yield 85-95%.

## 🎯 Next Steps

1. ✅ **Models working** with synthetic data
2. ⏳ **Train with real datasets** using Colab notebooks
3. ⏳ **Deploy to production** after validation
4. ⏳ **Monitor performance** in real-time

---

**Last Updated**: 2026-07-18  
**Maintainer**: SmartMaintain ML Team  
**Status**: Production Ready (Synthetic Models)
