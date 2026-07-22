# SmartMaintain Fine-Tuning Guide

## 🎯 Overview

This guide explains how to continuously improve ML models using production data **without including training code in your deployed application**.

### Architecture

```
┌─────────────────────────────────────────────┐
│  PRODUCTION (Your Deployed App)            │
│  ─────────────────────────────              │
│  ✅ Collects predictions + feedback         │
│  ✅ Stores in database                      │
│  ✅ Exports via API                         │
│  ✅ Loads pre-trained models                │
│  ❌ NO training happens here                │
└─────────────────────────────────────────────┘
                    ↓
            (Export dataset)
                    ↓
┌─────────────────────────────────────────────┐
│  EXTERNAL (Google Colab)                    │
│  ─────────────────────────────               │
│  ✅ Downloads production data               │
│  ✅ Fine-tunes models (GPU)                 │
│  ✅ Outputs new model files                 │
└─────────────────────────────────────────────┘
                    ↓
            (Upload new models)
                    ↓
┌─────────────────────────────────────────────┐
│  PRODUCTION (Hot Reload)                    │
│  ──────────────────────────                 │
│  ✅ Loads new models                        │
│  ✅ No restart needed                       │
│  ✅ Continues serving predictions           │
└─────────────────────────────────────────────┘
```

---

## 📋 Prerequisites

1. **Database migration applied** - Run `001_prediction_logging.sql`
2. **Admin JWT token** - For API access
3. **Google Colab account** - For external training
4. **Labeled production data** - Technicians add feedback

---

## 🚀 Quick Start (Complete Workflow)

### Step 1: Deploy Database Migration

```bash
# Connect to PostgreSQL
psql -U postgres -d smartmaintain

# Run migration
\i backend/ml/migrations/001_prediction_logging.sql
```

This creates:
- `prediction_log` table - Stores all predictions
- `prediction_feedback` table - Stores ground truth labels
- `training_data_export` view - Joins predictions + feedback

### Step 2: Predictions Are Logged Automatically

Every prediction is now automatically stored in the database:

```python
# This happens automatically in ml_service.py
# NO code changes needed!

# When you make a prediction:
POST /api/ml/predict
{
  "machine": "pompe",
  "sensors": {"vibration": 0.8, "pressure_in": 4.5}
}

# The service automatically logs:
# - Sensor inputs
# - Predicted defect
# - Confidence scores
# - Timestamp
```

### Step 3: Technicians Add Feedback

After maintenance, technicians label what the actual defect was:

```bash
# Add feedback via API
curl -X POST http://localhost:5000/api/ml/feedback/predictions/123/feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "actual_defect": "cavitation",
    "notes": "Confirmed during inspection",
    "severity": "high"
  }'
```

Or via batch import:

```bash
curl -X POST http://localhost:5000/api/ml/feedback/batch-feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "feedbacks": [
      {"prediction_id": 123, "actual_defect": "cavitation", "severity": "high"},
      {"prediction_id": 124, "actual_defect": "normal_operation"},
      {"prediction_id": 125, "actual_defect": "usure_garniture_mecanique"}
    ]
  }'
```

### Step 4: Check Statistics

Monitor how much labeled data you have:

```bash
curl http://localhost:5000/api/ml/feedback/statistics?machine=pompe \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "machine": "pompe",
  "total_predictions": 1250,
  "labeled_predictions": 85,
  "unlabeled_predictions": 1165,
  "correct_predictions": 78,
  "incorrect_predictions": 7,
  "accuracy": 91.76,
  "labeling_progress": 6.8
}
```

**Recommendation**: Aim for **100+ labeled samples** before fine-tuning.

### Step 5: Fine-Tune in Google Colab

Once you have enough labeled data (100+ samples recommended):

#### 5.1 Open Colab Notebook

1. Go to https://colab.research.google.com/
2. Upload: `backend/ml/models/notebooks/finetune_model_colab.ipynb`

#### 5.2 Configure API Access

Update the configuration cell:

```python
API_URL = "https://your-api.com"  # Your API URL
API_TOKEN = "your-jwt-token"      # Admin token
MACHINE_TYPE = "pompe"            # Machine to fine-tune
```

#### 5.3 Run All Cells

Click **Runtime → Run all**

The notebook will:
1. ✅ Download labeled production data from your API
2. ✅ Load your existing model files (upload them when prompted)
3. ✅ Combine original training data with production data
4. ✅ Fine-tune the model using incremental learning
5. ✅ Evaluate performance (before/after comparison)
6. ✅ Generate visualizations (confusion matrix, feature importance)
7. ✅ Save new model files

#### 5.4 Download New Model Files

The notebook automatically downloads:
- `pompe_xgb.pkl` - Fine-tuned model
- `pompe_scaler.pkl` - Feature scaler
- `pompe_label_encoder.pkl` - Label encoder
- `pompe_metadata.json` - Updated metadata

### Step 6: Deploy New Model

#### Option A: Manual Upload (Simple)

```bash
# 1. Copy new model files to server
scp pompe_*.pkl your-server:/path/to/smartmaintain/backend/ml/models/trained/
scp pompe_*.json your-server:/path/to/smartmaintain/backend/ml/models/trained/

# 2. Hot-reload the model (NO restart needed!)
curl -X POST http://localhost:5000/api/ml/reload?machine=pompe \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "success": true,
  "message": "Model for pompe reloaded successfully",
  "machine": "pompe",
  "model_name": "XGB-pompe-v2",
  "accuracy": 0.9456
}
```

#### Option B: Docker Volume (Automated)

```bash
# 1. Copy to Docker volume
docker cp pompe_*.pkl smartmaintain-ml:/app/models/trained/
docker cp pompe_*.json smartmaintain-ml:/app/models/trained/

# 2. Hot-reload
curl -X POST http://localhost:5000/api/ml/reload?machine=pompe \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Step 7: Verify New Model

```bash
# Check that the new model is active
curl http://localhost:5000/api/ml/reload/verify \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

Response:
```json
{
  "mock_mode": false,
  "loaded_models": {
    "pompe": {
      "model_name": "XGB-pompe-v2",
      "accuracy": 0.9456,
      "classes": ["normal_operation", "cavitation", "usure_garniture_mecanique"],
      "n_features": 27
    },
    ...
  },
  "count": 4
}
```

---

## 📊 API Endpoints Reference

### Predictions & Feedback

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ml/feedback/predictions` | GET | List recent predictions |
| `/api/ml/feedback/predictions?unlabeled_only=true` | GET | Get predictions needing labels |
| `/api/ml/feedback/predictions/{id}` | GET | Get specific prediction |
| `/api/ml/feedback/predictions/{id}/feedback` | POST | Add ground truth label |
| `/api/ml/feedback/batch-feedback` | POST | Add multiple labels at once |
| `/api/ml/feedback/statistics` | GET | Get accuracy statistics |

### Data Export (for Colab)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ml/feedback/export/training-data` | GET | Export labeled data (JSON) |
| `/api/ml/feedback/export/training-data?format=csv` | GET | Export as CSV |

Query params:
- `machine` - Filter by machine type
- `start_date` - Start date (ISO format)
- `end_date` - End date (ISO format)
- `min_confidence` - Minimum confidence threshold
- `include_incorrect` - Include wrong predictions (default: true)

### Model Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ml/reload` | POST | Reload all models |
| `/api/ml/reload?machine=pompe` | POST | Reload specific machine |
| `/api/ml/reload/verify` | GET | Check loaded models |

---

## 🔄 Recommended Fine-Tuning Schedule

### For New Deployments

| Week | Action | Goal |
|------|--------|------|
| Week 1-2 | Collect predictions | Gather baseline data |
| Week 3 | Add labels (50+) | Initial feedback collection |
| Week 4 | **First fine-tune** | Improve from synthetic→real data |
| Week 6 | Add labels (100+) | Continuous feedback |
| Week 8 | **Second fine-tune** | Further improvements |

### For Production Systems

- **Monthly fine-tuning** - Regular improvements
- **After major events** - Equipment failures, maintenance
- **Seasonal adjustments** - Operating condition changes
- **When accuracy drops** - Model drift detection

---

## 📈 Performance Monitoring

### Check Model Accuracy Over Time

```sql
-- Query database to track accuracy
SELECT 
  machine,
  DATE_TRUNC('week', pl.timestamp) as week,
  COUNT(*) as predictions,
  SUM(CASE WHEN pf.is_correct THEN 1 ELSE 0 END)::float / 
    NULLIF(COUNT(pf.id), 0) * 100 as accuracy
FROM prediction_log pl
LEFT JOIN prediction_feedback pf ON pl.id = pf.prediction_log_id
WHERE pl.machine = 'pompe'
GROUP BY machine, week
ORDER BY week DESC;
```

### Detect Model Drift

```bash
# Get weekly accuracy statistics
curl "http://localhost:5000/api/ml/feedback/statistics?machine=pompe" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Alert triggers**:
- Accuracy drops below 85%
- Confidence scores trending downward
- New defect classes appearing

---

## 🎓 Best Practices

### 1. **Catastrophic Forgetting Prevention**

Always combine original training data with production data:

```python
# In finetune_model_colab.ipynb
X_combined = np.vstack([X_original, X_production])
y_combined = np.concatenate([y_original, y_production])
```

Without original data, the model may "forget" rare defects.

### 2. **Incremental Learning**

Use warm-start to continue from existing model:

```python
model_finetuned.fit(
    X_train,
    y_train,
    xgb_model=model.get_booster()  # Start from existing model
)
```

This is faster and more stable than training from scratch.

### 3. **Class Balance**

Ensure balanced representation:

```python
# Check class distribution
unique, counts = np.unique(y_production, return_counts=True)
for cls, cnt in zip(unique, counts):
    print(f"{cls}: {cnt}")
```

Aim for **at least 20 samples per class** for fine-tuning.

### 4. **Validation Before Deployment**

Always verify accuracy improvement:

```python
old_accuracy = 0.92
new_accuracy = 0.95

if new_accuracy > old_accuracy:
    print("✅ Deploy new model")
else:
    print("❌ Keep existing model")
```

### 5. **Version Control**

Keep track of model versions:

```json
{
  "model_name": "XGB-pompe-v3",
  "previous_version": "XGB-pompe-v2",
  "previous_accuracy": 0.92,
  "accuracy": 0.95,
  "finetuned": true,
  "n_production_samples": 150
}
```

---

## 🐛 Troubleshooting

### Issue: No Production Data Available

**Symptom**: Colab notebook shows "No production data available"

**Solutions**:
1. Check predictions are being logged:
   ```sql
   SELECT COUNT(*) FROM prediction_log WHERE machine = 'pompe';
   ```

2. Add feedback labels via API

3. Verify database migration was applied

### Issue: Model Reload Fails

**Symptom**: `POST /api/ml/reload` returns error

**Solutions**:
1. Check file permissions:
   ```bash
   ls -la backend/ml/models/trained/
   ```

2. Verify all 4 files exist (`.pkl`, `.pkl`, `.pkl`, `.json`)

3. Check Docker logs:
   ```bash
   docker-compose logs ml
   ```

### Issue: Lower Accuracy After Fine-Tuning

**Symptom**: New model performs worse than old model

**Possible causes**:
- Not enough production samples (<100)
- Imbalanced classes
- Catastrophic forgetting (no original data)
- Overfitting on production data

**Solutions**:
1. Collect more labeled samples
2. Include original training data
3. Use lower learning rate (0.01 instead of 0.05)
4. Keep the old model deployed

### Issue: API Token Expired

**Symptom**: 401 Unauthorized error in Colab

**Solution**: Get a new JWT token:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password"}'
```

---

## 📁 File Structure

```
backend/ml/
├── migrations/
│   └── 001_prediction_logging.sql       # Database schema
├── models/
│   ├── prediction_log.py                # Data models
│   ├── notebooks/
│   │   └── finetune_model_colab.ipynb  # Fine-tuning notebook
│   └── trained/
│       ├── moteur_xgb.pkl
│       ├── pompe_xgb.pkl                # ← Replace these files
│       ├── compresseur_xgb.pkl
│       └── echangeur_xgb.pkl
├── services/
│   ├── ml_service.py                    # Auto-logs predictions
│   └── feedback_service.py              # Data collection
├── routes/
│   ├── feedback.py                      # Feedback API
│   └── reload.py                        # Hot-reload API
└── FINETUNING_GUIDE.md                  # This file
```

---

## 🎉 Summary

You now have a complete fine-tuning system that:

✅ **Collects data in production** - Automatic prediction logging  
✅ **NO training in production** - Keeps deployment lightweight  
✅ **External fine-tuning** - Uses Google Colab's free GPU  
✅ **Hot-reload models** - No downtime for updates  
✅ **Continuous improvement** - Models get better over time  

**Next steps**:
1. ✅ Deploy database migration
2. ✅ Start collecting predictions (automatic)
3. ✅ Add feedback labels (manual or batch)
4. ✅ Fine-tune when you have 100+ labels
5. ✅ Deploy and monitor improvements

---

**Questions?** Check the API logs or ML service logs:
```bash
docker-compose logs -f ml
```

**Created**: 2026-07-20  
**Author**: SmartMaintain ML Team
