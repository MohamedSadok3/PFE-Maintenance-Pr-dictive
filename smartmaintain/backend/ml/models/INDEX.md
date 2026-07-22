# ML Models - Quick Index

Complete ML training infrastructure for SmartMaintain predictive maintenance.

## 📚 Documentation Hub

| Document | Purpose | Audience |
|----------|---------|----------|
| **[README.md](README.md)** | Main overview & quick reference | Everyone |
| **[README_TRAINING.md](README_TRAINING.md)** | Detailed training guide | ML Engineers |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System architecture & data flow | Architects |

## 📁 Directory Overview

### [trained/](trained/)
**Purpose**: Production-ready model artifacts  
**Contents**: 16 files (4 per machine)  
**Used by**: RealMLEngine  
**Status**: ✅ All models trained and working

[📖 Read More](trained/README.md)

### [notebooks/](notebooks/)
**Purpose**: Google Colab training notebooks  
**Contents**: 3 Jupyter notebooks  
**Used for**: Training with real datasets  
**Status**: 📓 Ready to use

[📖 Read More](notebooks/README.md)

### [scripts/](scripts/)
**Purpose**: CLI training & testing scripts  
**Contents**: 2 Python scripts  
**Used for**: Local training & validation  
**Status**: 🔧 Production ready

[📖 Read More](scripts/README.md)

## 🚀 Quick Actions

### ✅ Verify Models Work
```bash
docker-compose exec ml python -c "
from services.ml_service import MLService
svc = MLService()
print('Models loaded:', list(svc.engine.models.keys()))
"
```

### 🔄 Train New Model
```bash
# Option 1: Upload to Google Colab
# notebooks/train_pompe_colab.ipynb

# Option 2: CLI (Docker)
docker-compose exec ml python /app/models/scripts/train_model.py --machine pompe
```

### 🧪 Test Predictions
```bash
docker-compose exec ml python /app/models/scripts/test_model.py
```

## 🎯 Machine Types

| Machine | Sensors | Defects | Accuracy |
|---------|---------|---------|----------|
| **moteur** | vibration, current | degradation_roulement, desequilibre_desalignement | 100% |
| **pompe** | vibration, pressure_in, pressure_out | cavitation, usure_garniture_mecanique | 100% |
| **compresseur** | pressure, current, temperature_oil | usure_soupapes, refroidissement_huile | 96.5% |
| **echangeur** | temp_in_hot, temp_out_hot, flow_rate | encrassement_progressif, fuite_interne | 92.5% |

## 📊 Feature Engineering

**9 statistical features per sensor:**
- max, min, mean, sd
- rms, skewness, kurtosis
- crest_factor, form_factor

**Window size**: 20 samples  
**Total features**: 9 × 3 sensors = 27 features

## 🔗 Related Documentation

### In This Repository
- [Backend ML Service](../README.md)
- [RealMLEngine](../engines/real_engine.py)
- [ML Service](../services/ml_service.py)

### External
- [Project Root](../../../README.md)
- [API Documentation](../../../docs/API.md)
- [Deployment Guide](../../../docs/DEPLOYMENT.md)

## 🎓 Training Resources

### Datasets
- [CWRU Bearing Data](https://engineering.case.edu/bearingdatacenter) - Motor bearings
- [Pump Sensor Data](https://www.kaggle.com/datasets/nphantawee/pump-sensor-data) - Pump failures
- [Compressor Data](https://www.kaggle.com/datasets/pythonkumar/compressor-data) - Compressor sensors

### Tools
- [Google Colab](https://colab.research.google.com/) - Free GPU training
- [Kaggle](https://www.kaggle.com/) - ML datasets
- [XGBoost Docs](https://xgboost.readthedocs.io/) - Model documentation

## 🐛 Troubleshooting

### Models not loading?
```bash
# Check files exist (should see 16 files)
docker-compose exec ml ls -la /app/models/trained/*.pkl

# Check RealMLEngine path
docker-compose exec ml python -c "
from engines.real_engine import RealMLEngine
print(RealMLEngine.MODELS_DIR)
"
```

### Still in mock mode?
```bash
# Verify environment
docker-compose exec ml env | grep MOCK_ML
# Should show: MOCK_ML=false

# Check service
docker-compose exec ml python -c "
from services.ml_service import MLService
print('Mock:', MLService().mock_ml)
"
```

### Training fails?
- Check logs: `docker-compose logs ml --tail=100`
- Verify dependencies: `docker-compose exec ml pip list | grep xgboost`
- See [README_TRAINING.md](README_TRAINING.md) troubleshooting section

## 📈 Performance

| Metric | Value |
|--------|-------|
| Inference time | <10ms per prediction |
| Model size | ~1.4MB total (all 4 machines) |
| Memory usage | ~50MB loaded in RAM |
| Accuracy | 92.5-100% (synthetic data) |
| Expected (real) | 85-95% |

## 🔄 Workflow Summary

### Development
1. Train with synthetic data (scripts)
2. Test locally
3. Deploy to dev environment

### Production
1. Train with real datasets (Colab)
2. Validate accuracy (>85%)
3. Deploy to production
4. Monitor performance

## 📦 File Counts

```
models/
├── Documentation:     6 files (*.md)
├── Trained Models:   16 files (4 × 4 machines)
├── Notebooks:         3 files (.ipynb)
└── Scripts:           2 files (.py)
───────────────────────────────────
Total:                27 files
```

## 🎯 Status Dashboard

- ✅ **Synthetic models**: All 4 machines trained and working
- ✅ **Infrastructure**: Training notebooks ready
- ✅ **Documentation**: Complete for all components
- ✅ **Deployment**: Docker volumes configured
- ⏳ **Real datasets**: Ready to train with Colab
- ⏳ **Production**: Pending real data validation

## 🚀 Getting Started

### New to this project?
1. Start with [README.md](README.md)
2. Understand [ARCHITECTURE.md](ARCHITECTURE.md)
3. Run test: `docker-compose exec ml python /app/models/scripts/test_model.py`

### Want to train models?
1. For quick testing: [scripts/README.md](scripts/README.md)
2. For production: [notebooks/README.md](notebooks/README.md)

### Need to deploy?
1. Verify [trained/README.md](trained/README.md)
2. Check docker-compose.yml volume mapping
3. Restart: `docker-compose restart ml`

---

**Version**: 1.0  
**Last Updated**: 2026-07-18  
**Maintained by**: SmartMaintain ML Team
