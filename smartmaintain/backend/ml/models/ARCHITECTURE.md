# ML Model Architecture - SmartMaintain

## 📐 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      SmartMaintain Platform                      │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │    Gateway Service        │
                    │   (API + WebSocket)       │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │     ML Service            │
                    │   (Flask + Redis)         │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │   MLService (Orchestrator)│
                    └─────────────┬─────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
    ┌─────────▼─────────┐               ┌───────────▼──────────┐
    │  MockMLEngine     │               │   RealMLEngine       │
    │  (Development)    │               │   (Production)       │
    └───────────────────┘               └───────────┬──────────┘
                                                    │
                        ┌───────────────────────────┴─────────────────┐
                        │        models/trained/                      │
                        │  ┌────────────────────────────────────┐    │
                        │  │  moteur_xgb.pkl                    │    │
                        │  │  moteur_scaler.pkl                 │    │
                        │  │  moteur_label_encoder.pkl          │    │
                        │  │  moteur_metadata.json              │    │
                        │  └────────────────────────────────────┘    │
                        │  ┌────────────────────────────────────┐    │
                        │  │  pompe_* (4 files)                 │    │
                        │  │  compresseur_* (4 files)           │    │
                        │  │  echangeur_* (4 files)             │    │
                        │  └────────────────────────────────────┘    │
                        └─────────────────────────────────────────────┘
```

## 🔄 Data Flow

### Training Phase

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Dataset    │────────▶│   Notebook   │────────▶│    Colab     │
│  (Kaggle)    │         │  (.ipynb)    │         │   Runtime    │
└──────────────┘         └──────────────┘         └──────┬───────┘
                                                          │
                         ┌────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Feature Extraction  │
              │  (9 stats × 3 sens)  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Preprocessing      │
              │  - Split 80/20       │
              │  - Encode labels     │
              │  - Scale features    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  XGBoost Training    │
              │  - 100 estimators    │
              │  - 5-fold CV         │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Export Artifacts    │
              │  - model.pkl         │
              │  - scaler.pkl        │
              │  - encoder.pkl       │
              │  - metadata.json     │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  models/trained/     │
              └──────────────────────┘
```

### Prediction Phase

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│ IoT Device   │────────▶│  IoT Service │────────▶│    Redis     │
│ (MQTT)       │         │              │         │  sensor_data │
└──────────────┘         └──────────────┘         └──────┬───────┘
                                                          │
                         ┌────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  ML Service          │
              │  consume_sensor_data │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  RealMLEngine        │
              │  predict()           │
              └──────────┬───────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌────────────────┐            ┌──────────────────┐
│ Load Model     │            │ Extract Features │
│ - XGBoost      │            │ - 9 stats        │
│ - Scaler       │            │ - 20 samples     │
│ - Encoder      │            │                  │
└────────┬───────┘            └─────────┬────────┘
         │                              │
         └──────────────┬───────────────┘
                        │
                        ▼
              ┌──────────────────────┐
              │  Normalize Features  │
              │  (StandardScaler)    │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  XGBoost Predict     │
              │  - Class probs       │
              │  - Confidence        │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Map Labels          │
              │  (LabelEncoder)      │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Publish Result      │
              │  Redis ml_predictions│
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Gateway → Frontend  │
              │  (WebSocket)         │
              └──────────────────────┘
```

## 🧠 Feature Engineering

### Input: Raw Sensor Data (Time Series)

```
Time Window (20 samples):
[s₀, s₁, s₂, ..., s₁₉]

Example - Vibration:
[0.15, 0.14, 0.16, 0.15, 0.17, ...]
```

### Transformation: Statistical Features (9 per sensor)

```python
features = {
    'max':      max(samples),                    # Peak value
    'min':      min(samples),                    # Minimum value
    'mean':     mean(samples),                   # Average
    'sd':       std(samples),                    # Standard deviation
    'rms':      sqrt(mean(samples²)),            # Root mean square
    'skewness': skew(samples),                   # Asymmetry
    'kurtosis': kurtosis(samples),               # Tailedness
    'crest':    max(|samples|) / rms,            # Crest factor
    'form':     rms / mean(|samples|)            # Form factor
}
```

### Output: Feature Vector

```
Machine: MOTEUR (3 sensors × 9 features = 27 features)

[vibration_max, vibration_min, vibration_mean, ...,
 current_max, current_min, current_mean, ...,
 temperature_max, temperature_min, ...]
```

## 🎯 Model Architecture

### XGBoost Configuration

```python
XGBClassifier(
    objective='multi:softprob',    # Multi-class classification
    n_estimators=100,              # 100 decision trees
    max_depth=6,                   # Maximum tree depth
    learning_rate=0.1,             # Step size shrinkage
    subsample=0.8,                 # Row sampling
    colsample_bytree=0.8,          # Column sampling
    random_state=42,               # Reproducibility
)
```

### Decision Tree Ensemble

```
Tree 1:          Tree 2:          ...          Tree 100:
   ┌─┐              ┌─┐                          ┌─┐
   │?│              │?│                          │?│
  ┌┴─┴┐            ┌┴─┴┐                        ┌┴─┴┐
  │   │            │   │                        │   │
 ┌┴┐ ┌┴┐          ┌┴┐ ┌┴┐                      ┌┴┐ ┌┴┐
 │C│ │C│          │C│ │C│          ...         │C│ │C│
 └─┘ └─┘          └─┘ └─┘                      └─┘ └─┘

         Weighted Average → Final Prediction
```

### Prediction Output

```python
{
    "machine": "moteur",
    "defect": "degradation_roulement",      # Predicted class
    "defect_score": 0.85,                   # 1 - P(normal)
    "confidence": 0.92,                     # P(predicted class)
    "defect_scores": {
        "normal_operation": 0.08,
        "degradation_roulement": 0.85,
        "desequilibre_desalignement": 0.07
    },
    "required_sensors": ["vibration", "current"],
    "model_name": "XGBoost-moteur-v1"
}
```

## 📊 Model Comparison

### Moteur (Motor)

```
Input:  vibration (mm/s), current (A)
Output: normal_operation, degradation_roulement, desequilibre_desalignement

Dataset: CWRU Bearing (real) or Synthetic
Samples: 2000 (666 per class)
Features: 9 statistical × 2 sensors = 18 features
Accuracy: 100% (synthetic) | 85-95% (real expected)
```

### Pompe (Pump)

```
Input:  vibration (mm/s), pressure_in (bar), pressure_out (bar)
Output: normal_operation, cavitation, usure_garniture_mecanique

Dataset: Pump Sensor Data (Kaggle)
Samples: Variable (from dataset)
Features: 9 statistical × 3 sensors = 27 features
Accuracy: 100% (synthetic) | 85-95% (real expected)
```

### Compresseur (Compressor)

```
Input:  pressure (bar), current (A), temperature_oil (°C)
Output: normal_operation, usure_soupapes, refroidissement_huile

Dataset: Compressor Data (Kaggle)
Samples: Variable (from dataset)
Features: 9 statistical × 3 sensors = 27 features
Accuracy: 96.5% (synthetic) | 85-95% (real expected)
```

### Echangeur (Heat Exchanger)

```
Input:  temp_in_hot (°C), temp_out_hot (°C), flow_rate (L/min)
Output: normal_operation, encrassement_progressif, fuite_interne

Dataset: Physics-based Synthetic
Samples: 3000 (1000 per class)
Features: 9 statistical × 3 sensors = 27 features
Accuracy: 92.5% (synthetic) | 85-95% (real expected)
```

## 🔧 Training Pipeline Details

### Stage 1: Data Collection

```
Source          Format          Size        Quality
────────────────────────────────────────────────────
Kaggle          CSV/NPZ         1-100MB     High
CWRU            MAT/NPZ         50-200MB    High
Synthetic       Generated       N/A         Medium
```

### Stage 2: Feature Extraction

```
Window Size: 20 samples
Overlap: 0% (non-overlapping windows)
Sampling Rate: Variable (depends on IoT config)

For each sensor channel:
  Extract 9 statistical features
  Total features = n_sensors × 9
```

### Stage 3: Preprocessing

```
1. Label Encoding
   Classes → [0, 1, 2]
   
2. Train/Test Split
   80% train, 20% test
   Stratified (balanced classes)
   
3. Feature Scaling
   StandardScaler: z = (x - μ) / σ
   Fit on train, transform train+test
```

### Stage 4: Training

```
XGBoost Training Loop:
  For tree in 1..100:
    1. Calculate gradients
    2. Build tree structure
    3. Update predictions
    4. Apply regularization
```

### Stage 5: Validation

```
5-Fold Cross-Validation:
  Fold 1: ████████░░ → 89%
  Fold 2: █████████░ → 91%
  Fold 3: ████████░░ → 88%
  Fold 4: █████████░ → 92%
  Fold 5: ████████░░ → 90%
  
  Mean: 90.0% (±1.5%)
```

### Stage 6: Export

```
Artifacts:
  model.pkl        ← XGBoost trained model
  scaler.pkl       ← StandardScaler (μ, σ)
  encoder.pkl      ← LabelEncoder (class mapping)
  metadata.json    ← Model info + metrics
```

## 📦 File Structure

```
models/
├── trained/                    # Production models
│   ├── moteur_xgb.pkl         # 250KB - XGBoost binary
│   ├── moteur_scaler.pkl      # 1KB - Normalization params
│   ├── moteur_label_encoder.pkl # 0.5KB - Class mapping
│   ├── moteur_metadata.json   # 0.5KB - Model info
│   └── [pompe, compresseur, echangeur] × 4 files each
│
├── notebooks/                  # Training notebooks
│   ├── train_pompe_colab.ipynb
│   ├── train_compresseur_colab.ipynb
│   └── train_echangeur_colab.ipynb
│
└── scripts/                    # Automation scripts
    ├── train_model.py          # CLI trainer
    └── test_model.py           # Model tester
```

## 🚀 Deployment

### Docker Volume Mapping

```yaml
ml:
  volumes:
    - ./backend/ml/models/trained:/app/models/trained
```

### RealMLEngine Initialization

```python
MODELS_DIR = Path("/app/models/trained")

def __init__(self):
    self.models = {}
    self.scalers = {}
    self.label_encoders = {}
    
    for machine in ["moteur", "pompe", "compresseur", "echangeur"]:
        self.models[machine] = joblib.load(MODELS_DIR / f"{machine}_xgb.pkl")
        self.scalers[machine] = joblib.load(MODELS_DIR / f"{machine}_scaler.pkl")
        self.label_encoders[machine] = joblib.load(MODELS_DIR / f"{machine}_label_encoder.pkl")
```

## 📈 Performance Metrics

| Metric | Moteur | Pompe | Compresseur | Echangeur |
|--------|--------|-------|-------------|-----------|
| **Accuracy** | 100% | 100% | 96.5% | 92.5% |
| **Precision** | 1.00 | 1.00 | 0.96 | 0.92 |
| **Recall** | 1.00 | 1.00 | 0.96 | 0.92 |
| **F1-Score** | 1.00 | 1.00 | 0.96 | 0.92 |
| **Inference Time** | <10ms | <10ms | <10ms | <10ms |
| **Model Size** | 250KB | 246KB | 447KB | 486KB |

---

**Architecture Version**: v1.0  
**Last Updated**: 2026-07-18  
**Maintained by**: SmartMaintain ML Team
