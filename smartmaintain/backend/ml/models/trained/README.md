# Trained Models Directory

This directory contains all trained model artifacts loaded by RealMLEngine.

## 📦 Contents

### Current Models (16 files)

```
trained/
├── moteur_xgb.pkl               # Motor XGBoost model
├── moteur_scaler.pkl            # Motor feature scaler
├── moteur_label_encoder.pkl     # Motor class encoder
├── moteur_metadata.json         # Motor model metadata
│
├── pompe_xgb.pkl                # Pump XGBoost model
├── pompe_scaler.pkl             # Pump feature scaler
├── pompe_label_encoder.pkl      # Pump class encoder
├── pompe_metadata.json          # Pump model metadata
│
├── compresseur_xgb.pkl          # Compressor XGBoost model
├── compresseur_scaler.pkl       # Compressor feature scaler
├── compresseur_label_encoder.pkl # Compressor class encoder
├── compresseur_metadata.json    # Compressor model metadata
│
├── echangeur_xgb.pkl            # Heat exchanger XGBoost model
├── echangeur_scaler.pkl         # Heat exchanger feature scaler
├── echangeur_label_encoder.pkl  # Heat exchanger class encoder
└── echangeur_metadata.json      # Heat exchanger model metadata
```

## 🔒 File Requirements

**Each machine requires exactly 4 files:**

1. `{machine}_xgb.pkl` - XGBoost classifier (~250-500KB)
2. `{machine}_scaler.pkl` - StandardScaler (~1-2KB)
3. `{machine}_label_encoder.pkl` - LabelEncoder (~0.5-1KB)
4. `{machine}_metadata.json` - Model info (~0.5KB)

**Missing any file will cause RealMLEngine to fail on startup.**

## 🚀 Adding New Models

### From Colab Training

```bash
# 1. Download 4 files from Colab
# 2. Copy to this directory
cp ~/Downloads/{machine}_*.pkl ./
cp ~/Downloads/{machine}_*.json ./

# 3. Restart ML service
docker-compose restart ml
```

### From Local Training

```bash
# Train locally
docker-compose exec ml python /app/models/scripts/train_model.py --machine pompe

# Files are saved automatically to /app/models/trained/
```

## 🔍 Verifying Files

```bash
# Check all files exist
ls -la *.pkl *.json | wc -l
# Should output: 16

# Check file sizes
du -h *.pkl
# XGBoost models: ~200-500KB each
# Scalers: ~1-2KB each
# Encoders: ~0.5-1KB each

# Validate model loads
docker-compose exec ml python -c "
import joblib
model = joblib.load('/app/models/trained/moteur_xgb.pkl')
print(f'Model type: {type(model).__name__}')
print(f'Features: {model.n_features_in_}')
"
```

## 📊 Model Metadata

Each `{machine}_metadata.json` contains:

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
  "n_samples_test": 400,
  "cv_mean": 0.99,
  "cv_std": 0.01
}
```

## 🔄 Versioning

### Backup Before Update

```bash
# Create backup
mkdir -p backup/$(date +%Y%m%d)
cp *.pkl *.json backup/$(date +%Y%m%d)/
```

### Version Naming

```
{machine}_xgb_v1.pkl       # Initial version
{machine}_xgb_v2.pkl       # After retraining
{machine}_xgb_prod.pkl     # Current production
```

Currently using unversioned names (latest is always used).

## ⚠️ Important Notes

### Do Not Commit to Git

Large `.pkl` files should not be committed to version control:

```gitignore
# Already in .gitignore
*.pkl
```

Use Git LFS or external storage for model versioning.

### File Corruption

If models fail to load:

```bash
# Check file integrity
file moteur_xgb.pkl
# Should output: data

# Try loading manually
python -c "import joblib; joblib.load('moteur_xgb.pkl')"
```

### Permissions

Ensure files are readable by Docker container:

```bash
chmod 644 *.pkl *.json
```

## 🎯 Model Status

| Machine | Version | Date | Status | Size |
|---------|---------|------|--------|------|
| moteur | v1 | 2026-07-18 | ✅ Active | 250KB |
| pompe | v1 | 2026-07-18 | ✅ Active | 246KB |
| compresseur | v1 | 2026-07-18 | ✅ Active | 447KB |
| echangeur | v1 | 2026-07-18 | ✅ Active | 486KB |

**Total Size**: ~1.4MB

---

**Path**: `/app/models/trained/` (inside container)  
**Mounted from**: `backend/ml/models/trained/`  
**Loaded by**: `engines/real_engine.py`
