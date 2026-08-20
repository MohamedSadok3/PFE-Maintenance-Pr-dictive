# SmartMaintain V7 Model Integration Guide

## Overview

This document describes the successful integration of SmartMaintain V7 models into the backend ML service. V7 models use **simplified input contracts** that accept raw sensor data instead of pre-computed features.

## What's New in V7

### Simplified Input Requirements

| Equipment | V6 Input | V7 Input |
|-----------|----------|----------|
| **Moteur** | 27 VBL features (pre-computed) | 100,000 vibration samples (5s @ 20kHz) |
| **Pompe** | 80 features OR 8 SKAB sensors × 20 | 4 sensors × 20 measurements |
| **Compresseur** | 150 features OR 15 MetroPT sensors × 30 | 3 sensors × 30 measurements |
| **Échangeur** | 130 features OR 5 sensors × 30 | 5 sensors × 30 measurements |

### Key Benefits

1. **Simpler API contracts** - Users provide raw sensor data, not statistical features
2. **Automatic feature extraction** - Features computed internally by the service
3. **Consistent interface** - All equipment types use sensor arrays
4. **High performance** - Maintained or improved model accuracy

## Architecture

### Component Structure

```
smartmaintain/backend/ml/
├── models_v7/                      # V7 model bundles
│   ├── moteur/
│   ├── pompe/
│   ├── compresseur/
│   └── echangeur/
├── engines/
│   ├── feature_extractor_v7.py     # Feature extraction utilities
│   └── unified_engine.py           # Multi-version engine
├── services/
│   ├── model_service.py            # V6 model service (existing)
│   ├── model_service_v7.py         # V7 model service (new)
│   └── ml_service.py               # Updated for version routing
└── test_v7_integration.py          # Comprehensive test suite
```

### Class Hierarchy

```
UnifiedMLEngine
├── ModelService (V6)
│   └── LoadedBundle
└── ModelServiceV7 (V7)
    └── LoadedBundleV7
        └── FeatureExtractorV7
```

## Usage

### Configuration

Set the default model version via environment variable:

```bash
# Use V7 by default
export ML_MODEL_VERSION=v7

# Use V6 by default (backward compatible)
export ML_MODEL_VERSION=v6
```

### API Requests

#### V7 Prediction Example (Motor)

```python
import requests

# Motor prediction with raw vibration data
response = requests.post("http://localhost:5002/api/ml/predict", json={
    "equipment_type": "moteur",
    "model_version": "v7",  # Specify V7
    "sensors": {
        "vibration": [0.1, 0.11, 0.09, ...]  # 100,000 samples
    }
})
```

#### V7 Prediction Example (Pump)

```python
response = requests.post("http://localhost:5002/api/ml/predict", json={
    "equipment_type": "pompe",
    "model_version": "v7",
    "sensors": {
        "vibration": [0.1, 0.12, ...],      # 20 values
        "pressure": [5.2, 5.3, ...],        # 20 values
        "temperature": [62.0, 62.5, ...],   # 20 values
        "flow_rate": [16.0, 16.2, ...]      # 20 values
    }
})
```

#### V6 Prediction (Backward Compatible)

```python
# V6 still works with pre-computed features
response = requests.post("http://localhost:5002/api/ml/predict", json={
    "equipment_type": "moteur",
    "model_version": "v6",  # or omit for default
    "features": {
        "vbl_feature_1_mean_x": 0.123,
        # ... 27 features total
    }
})
```

### Status Endpoint

```python
# Get status for all versions
response = requests.get("http://localhost:5002/api/ml/status")

# Get status for specific version
response = requests.get("http://localhost:5002/api/ml/status?version=v7")
```

## Model Performance

### V7 Model Metrics

| Equipment | Clean Accuracy | Robust Accuracy | Min Class Recall | Estimator |
|-----------|---------------|-----------------|------------------|-----------|
| **Moteur** | 99.87% | 98.23% | 96.78% | ExtraTreesClassifier |
| **Pompe** | 100.00% | 99.77% | 99.30% | RandomForestClassifier |
| **Compresseur** | 99.34% | 92.03% | 76.27% | ExtraTreesClassifier |
| **Échangeur** | 98.33% | 97.99% | 94.87% | RandomForestClassifier |

**Note:** These are internal validation metrics. External industrial certification is required before production deployment.

## Feature Extraction Details

### Motor (Moteur)

**Input:** `vibration` - 100,000 samples @ 20 kHz
**Output:** 9 FFT-based features
- FFT mean, std, shape factor
- RMS, impulse factor
- Peak-to-peak, kurtosis
- Crest factor, skewness

### Pump (Pompe)

**Input:** 4 sensors × 20 measurements
- `vibration`, `pressure`, `temperature`, `flow_rate`
**Output:** 40 statistical features (10 per sensor)

### Compressor (Compresseur)

**Input:** 3 sensors × 30 measurements
- `pressure`, `temperature_oil`, `current`
**Output:** 30 statistical features (10 per sensor)

### Heat Exchanger (Échangeur)

**Input:** 5 raw sensors × 30 measurements
- `temp_in_hot`, `temp_out_hot`, `temp_in_cold`, `temp_out_cold`, `flow_rate`
**Derived:** 8 thermodynamic features computed internally
- `delta_hot`, `delta_cold`, `approach_hot`, `approach_cold`
- `effectiveness_proxy`, `heat_duty_hot`, `heat_duty_cold`, `energy_imbalance`
**Output:** 130 features (10 stats × 13 total sensors)

### Statistical Features (Applied to Each Sensor)

1. **min** - Minimum value
2. **max** - Maximum value
3. **mean** - Average value
4. **std** - Standard deviation
5. **rms** - Root mean square
6. **peak_to_peak** - Range (max - min)
7. **crest** - Peak-to-RMS ratio
8. **slope** - Linear trend
9. **q25** - First quartile (25th percentile)
10. **q75** - Third quartile (75th percentile)

## Error Handling

### Common Errors

#### 1. Insufficient Data

```json
{
  "error": "acquisition_insuffisante",
  "message": "Insufficient measurements: got 15, need 20",
  "equipment_type": "pompe",
  "received": 15,
  "required": 20,
  "status": "acquisition_continue"
}
```

**HTTP Status:** 202 (Accepted - continue acquiring data)

#### 2. Missing Sensors

```json
{
  "error": "invalid_feature_value",
  "message": "Missing required sensors: ['temperature']",
  "equipment_type": "pompe",
  "required_sensors": ["vibration", "pressure", "temperature", "flow_rate"]
}
```

**HTTP Status:** 422 (Unprocessable Entity)

#### 3. Wrong Window Size

```json
{
  "error": "invalid_series_length",
  "message": "Too many measurements: got 150000, expected exactly 100000",
  "equipment_type": "moteur",
  "received": 150000,
  "required": 100000
}
```

**HTTP Status:** 422 (Unprocessable Entity)

## Testing

### Run Integration Tests

```bash
cd smartmaintain/backend
python ml/test_v7_integration.py
```

### Test Coverage

The test suite validates:
1. ✅ Feature extraction for all equipment types
2. ✅ Model loading and bundle validation
3. ✅ Prediction accuracy and response format
4. ✅ Error handling (missing data, wrong size, invalid equipment)
5. ✅ Status endpoint responses

**All tests passed successfully!**

## Migration Guide

### For Existing V6 Users

1. **No breaking changes** - V6 continues to work exactly as before
2. **Gradual migration** - Test V7 on specific equipment types
3. **Version parameter** - Add `"model_version": "v7"` to requests
4. **Input format change** - Switch from features to raw sensors

### Example Migration

**Before (V6):**
```python
{
    "equipment_type": "pompe",
    "features": {
        "Accelerometer1RMS_min": 0.05,
        "Accelerometer1RMS_max": 0.15,
        # ... 78 more features
    }
}
```

**After (V7):**
```python
{
    "equipment_type": "pompe",
    "model_version": "v7",
    "sensors": {
        "vibration": [0.08, 0.09, 0.10, ...],  # 20 values
        "pressure": [5.2, 5.3, 5.1, ...],
        "temperature": [62, 63, 62, ...],
        "flow_rate": [16, 16.5, 15.8, ...]
    }
}
```

## Deployment

### Environment Variables

```bash
# Required
ML_MODEL_VERSION=v7              # Default model version (v6 or v7)

# Optional (uses defaults if not set)
ML_PORT=5002                     # ML service port
REDIS_URL=redis://localhost:6379 # Redis connection
```

### Docker Deployment

The existing Docker setup works without changes. Just set the environment variable:

```yaml
# docker-compose.yml
ml:
  environment:
    - ML_MODEL_VERSION=v7
```

## Known Limitations

1. **Motor V6 compatibility** - V6 motor model only accepts pre-computed features (not raw vibration)
2. **Data format validation** - V7 strictly validates window sizes and sensor presence
3. **Performance** - Motor predictions may be slower due to FFT computation
4. **Training data** - Some V7 fault classes use simulated or proxy data (documented in metadata)

## Support

### Model Metadata

Each model bundle includes:
- `metadata.json` - Model configuration and provenance
- `metrics.json` - Performance metrics and evaluation protocol
- `model_bundle.joblib` - Trained model with all parameters

### Logs

Check ML service logs for detailed error messages:
```bash
# View logs
docker logs smartmaintain-ml-1

# Follow logs
docker logs -f smartmaintain-ml-1
```

## Future Enhancements

Potential improvements for V8:
1. Support variable window sizes
2. Real-time streaming predictions
3. Model retraining interface
4. Multi-equipment fusion models
5. Confidence calibration
6. Explainable AI features

---

**Version:** V7.0 (2026-08-17)  
**Status:** Integration Complete ✅  
**Test Results:** 5/5 Passed 🎉
