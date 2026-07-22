# Training Notebooks

Google Colab notebooks for training ML models with real datasets.

## 📓 Available Notebooks

### 1. train_pompe_colab.ipynb
**Machine**: Pump  
**Dataset**: [Pump Sensor Data](https://www.kaggle.com/datasets/nphantawee/pump-sensor-data) (Kaggle)  
**Defects**: cavitation, usure_garniture_mecanique  
**Sensors**: vibration, pressure_in, pressure_out  
**Training Time**: ~10 minutes  
**Expected Accuracy**: 85-95%

### 2. train_compresseur_colab.ipynb
**Machine**: Compressor  
**Dataset**: [Compressor Data](https://www.kaggle.com/datasets/pythonkumar/compressor-data) (Kaggle)  
**Defects**: usure_soupapes, refroidissement_huile  
**Sensors**: pressure, current, temperature_oil  
**Training Time**: ~10 minutes  
**Expected Accuracy**: 85-95%

### 3. train_echangeur_colab.ipynb
**Machine**: Heat Exchanger  
**Dataset**: Synthetic (physics-based)  
**Defects**: encrassement_progressif, fuite_interne  
**Sensors**: temp_in_hot, temp_out_hot, flow_rate  
**Training Time**: ~5 minutes  
**Expected Accuracy**: 85-95%

## 🚀 Quick Start

### Prerequisites

1. **Google account** (free)
2. **Kaggle API token** (for pompe & compresseur)
   - Go to https://www.kaggle.com/settings
   - Click "Create New API Token"
   - Download `kaggle.json`

### Steps

1. **Open Google Colab**: https://colab.research.google.com/

2. **Upload notebook**: 
   - Click "Upload notebook"
   - Select one of the `.ipynb` files from this directory

3. **Run all cells**:
   - Menu: Runtime → Run all
   - Or: Ctrl+F9 (Windows/Linux) / Cmd+F9 (Mac)

4. **Upload kaggle.json** (when prompted for pompe/compresseur)

5. **Wait for training** (~5-10 minutes)

6. **Download output files**:
   - `{machine}_xgb.pkl`
   - `{machine}_scaler.pkl`
   - `{machine}_label_encoder.pkl`
   - `{machine}_metadata.json`

7. **Copy to project**:
   ```bash
   cp ~/Downloads/{machine}_*.pkl ../trained/
   cp ~/Downloads/{machine}_*.json ../trained/
   ```

8. **Restart service**:
   ```bash
   docker-compose restart ml
   ```

## 📋 Notebook Structure

Each notebook follows this structure:

### 1. Setup & Installation
```python
!pip install xgboost scikit-learn joblib kaggle
```

### 2. Data Loading
- Download from Kaggle (pompe, compresseur)
- Generate synthetic (echangeur)

### 3. Feature Engineering
- Extract 9 statistical features per sensor
- Create time windows (20 samples)

### 4. Preprocessing
- Train/test split (80/20)
- Label encoding
- Feature scaling

### 5. Model Training
- XGBoost classifier
- 5-fold cross-validation

### 6. Evaluation
- Confusion matrix
- Feature importance
- Classification report

### 7. Export
- Save 4 model artifacts
- Generate visualizations

## 🎯 Expected Outputs

### Model Files (4 per machine)
- `{machine}_xgb.pkl` (~200-500KB)
- `{machine}_scaler.pkl` (~1-2KB)
- `{machine}_label_encoder.pkl` (~0.5-1KB)
- `{machine}_metadata.json` (~0.5KB)

### Visualizations
- `{machine}_confusion_matrix.png`
- `{machine}_feature_importance.png`
- `{machine}_data_distribution.png` (echangeur only)

## 🔧 Customization

### Adjust Hyperparameters

```python
model = XGBClassifier(
    n_estimators=100,      # Increase for better accuracy
    max_depth=6,           # Increase for more complex patterns
    learning_rate=0.1,     # Decrease for smoother learning
    random_state=42,
)
```

### Change Window Size

```python
WINDOW_SIZE = 20  # Increase for more context
```

### Add More Features

```python
def extract_features_from_window(window_data, sensor_col):
    # Add frequency-domain features
    fft_vals = np.fft.fft(values)
    features['spectrum_peak'] = np.max(np.abs(fft_vals))
    return features
```

## 🐛 Troubleshooting

### Kaggle API Error
```
OSError: Could not find kaggle.json
```
**Solution**: Upload `kaggle.json` file when prompted by notebook

### Out of Memory
```
ResourceExhaustedError: OOM when allocating tensor
```
**Solution**: 
- Reduce `n_samples` in data generation
- Use Runtime → Factory reset runtime
- Upgrade to Colab Pro for more RAM

### Low Accuracy (<80%)
**Solutions**:
- Check class balance (should be roughly equal)
- Increase training data
- Tune hyperparameters
- Verify sensor data quality

### Dataset Not Found
```
404 - Dataset not found
```
**Solution**: 
- Verify dataset URL is correct
- Check dataset is still public
- Try manual download from Kaggle

## 📊 Performance Tips

### Faster Training
```python
model = XGBClassifier(
    n_estimators=50,       # Reduce trees
    max_depth=4,           # Reduce depth
    n_jobs=-1,             # Use all CPU cores
)
```

### Better Accuracy
```python
# More data
n_samples = 5000  # Instead of 2000

# Better validation
cv_scores = cross_val_score(model, X_train, y_train, cv=10)  # 10-fold
```

## 🔗 Resources

### Documentation
- [XGBoost Docs](https://xgboost.readthedocs.io/)
- [Scikit-learn Guide](https://scikit-learn.org/stable/user_guide.html)
- [Google Colab FAQ](https://research.google.com/colaboratory/faq.html)

### Datasets
- [Kaggle Datasets](https://www.kaggle.com/datasets)
- [UCI ML Repository](https://archive.ics.uci.edu/ml/index.php)
- [CWRU Bearing Data](https://engineering.case.edu/bearingdatacenter)

### Tutorials
- [Feature Engineering](https://www.kaggle.com/learn/feature-engineering)
- [Machine Learning](https://www.kaggle.com/learn/intro-to-machine-learning)
- [XGBoost Tutorial](https://xgboost.readthedocs.io/en/stable/tutorials/index.html)

## 📝 Notes

- **Free Colab limits**: 12 hours per session, GPU may not be available
- **Colab Pro**: $9.99/month, faster GPUs, longer sessions
- **Save frequently**: Colab sessions can disconnect
- **Download immediately**: Files are deleted after session ends

---

**Total Training Time**: ~25 minutes (all 3 notebooks)  
**Cost**: Free (with Google account)  
**Difficulty**: Beginner-friendly (just run cells)
