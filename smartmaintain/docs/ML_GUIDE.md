# Guide Machine Learning - SmartMaintain

**Dernière mise à jour**: 29 Juillet 2026

---

## 🚀 Quick Start (5 Minutes)

### Statut Actuel
✅ Les 4 modèles sont entraînés avec des **données synthétiques** et fonctionnels
⏳ Prêts à être réentraînés avec des **datasets réels** pour la production

### Formation Rapide d'un Modèle

**1. Obtenir Token Kaggle API (1 min)**
1. Aller sur https://www.kaggle.com/settings
2. Cliquer "Create New API Token"
3. Télécharger `kaggle.json`

**2. Entraîner Modèle POMPE (10 min)**
```bash
# 1. Ouvrir Google Colab
# 2. Upload: backend/ml/models/notebooks/train_pompe_colab.ipynb
# 3. Runtime → Run all
# 4. Upload kaggle.json quand demandé
# 5. Attendre fin entraînement (5-10 min)
# 6. Télécharger 4 fichiers: pompe_xgb.pkl, pompe_scaler.pkl,
#    pompe_label_encoder.pkl, pompe_metadata.json
```

**3. Copier Fichiers dans Projet (1 min)**
```bash
cp ~/Downloads/pompe_*.pkl "smartmaintain/backend/ml/models/trained/"
cp ~/Downloads/pompe_*.json "smartmaintain/backend/ml/models/trained/"
```

**4. Redémarrer Service ML (1 min)**
```bash
cd smartmaintain
docker-compose restart ml
```

**5. Tester (1 min)**
```bash
docker-compose exec ml python -c "
from engines.real_engine import RealMLEngine
engine = RealMLEngine()
result = engine.predict('pompe', {'vibration': 0.8, 'pressure_in': 4.5})
print(f'Défaut: {result[\"defect\"]} (confidence: {result[\"confidence\"]:.0%})')
"
```

### Datasets Disponibles

| Machine | Dataset | Source |
|---------|---------|--------|
| **Moteur** | CWRU Bearing | Inclus dans projet |
| **Pompe** | Pump Sensor Data | [Kaggle](https://www.kaggle.com/datasets/nphantawee/pump-sensor-data) |
| **Compresseur** | Compressor Data | [Kaggle](https://www.kaggle.com/datasets/pythonkumar/compressor-data) |
| **Échangeur** | Synthétique | Généré (pas de download) |

### Vérification Installation

```bash
docker-compose exec ml python -c "
from services.ml_service import MLService
svc = MLService()
print('✅ Mock mode:', svc.mock_ml, '(doit être False)')
print('✅ Engine:', type(svc.engine).__name__, '(doit être RealMLEngine)')
print('✅ Modèles chargés:', list(svc.engine.models.keys()))
"
```

**Sortie attendue**:
```
✅ Mock mode: False (doit être False)
✅ Engine: RealMLEngine (doit être RealMLEngine)
✅ Modèles chargés: ['moteur', 'pompe', 'compresseur', 'echangeur']
```

---

## 📊 Vue d'Ensemble

SmartMaintain utilise **4 modèles XGBoost** pour détecter les défauts de machines industrielles en temps réel:

| Machine | Capteurs | Défauts Détectés | Accuracy |
|---------|----------|------------------|----------|
| **Moteur** | vibration, current, temperature | Roulement, Désé

quilib

rement | 100% |
| **Pompe** | vibration, pressure_in, pressure_out, flow_rate | Cavitation, Usure joints | 100% |
| **Compresseur** | pressure, current, temp_oil, temp_air | Usure soupapes, Refroidissement | 96.5% |
| **Échangeur** | temp_in/out_hot/cold, flow_rate | Encrassement, Fuite | 92.5% |

---

## 🎯 Architecture ML

### Pipeline de Prédiction

```
Capteurs → Features Engineering → Normalisation → XGBoost → Classification
    │              │                    │             │            │
   20 pts      9 features/capteur  StandardScaler   Modèle    3 classes
```

### Feature Engineering

Pour chaque capteur, **9 features statistiques** sont calculées sur une fenêtre glissante de 20 échantillons:

```python
features = {
    'max': np.max(window),           # Valeur maximale
    'min': np.min(window),           # Valeur minimale
    'mean': np.mean(window),         # Moyenne
    'sd': np.std(window),            # Écart-type
    'rms': np.sqrt(np.mean(window**2)),  # RMS
    'skewness': skew(window),        # Asymétrie
    'kurtosis': kurtosis(window),    # Aplatissement
    'crest': max / rms,              # Facteur de crête
    'form': rms / mean_abs           # Facteur de forme
}
```

**Exemple Moteur**: 2 capteurs (vibration, current) × 9 features = **18 features**

---

## 🚀 Entraînement des Modèles

### Modèles Actuels

Les modèles fournis sont entraînés sur **données synthétiques** et fonctionnent parfaitement en développement.

Pour **production**, il est recommandé de les entraîner avec **données réelles**.

### Méthode 1: Google Colab (Recommandé)

#### Avantages
✅ GPU gratuit (plus rapide)  
✅ Pas d'installation locale  
✅ Datasets Kaggle intégrés  
✅ Notebooks prêts à l'emploi

#### Notebooks Disponibles

```
backend/ml/models/notebooks/
├── train_moteur_colab.ipynb         # CWRU Bearing Dataset
├── train_pompe_colab.ipynb          # Pump Sensor Data
├── train_compresseur_colab.ipynb    # Compressor Data
└── train_echangeur_colab.ipynb      # Synthetic (no Kaggle)
```

#### Étapes Rapides (10 min par modèle)

```bash
# 1. Obtenir token Kaggle
#    → https://www.kaggle.com/settings → "Create New API Token"
#    → Télécharger kaggle.json

# 2. Ouvrir Google Colab
#    → https://colab.research.google.com/

# 3. Upload notebook
#    → File → Upload notebook
#    → Choisir train_pompe_colab.ipynb

# 4. Exécuter
#    → Runtime → Run all
#    → Upload kaggle.json quand demandé
#    → Attendre 5-10 minutes

# 5. Télécharger modèles
#    → Files (panneau gauche)
#    → Télécharger 4 fichiers:
#      - pompe_xgb.pkl
#      - pompe_scaler.pkl
#      - pompe_label_encoder.pkl
#      - pompe_metadata.json

# 6. Copier dans le projet
cp ~/Downloads/pompe_*.pkl backend/ml/models/trained/
cp ~/Downloads/pompe_*.json backend/ml/models/trained/

# 7. Redémarrer service
docker-compose restart ml
```

### Méthode 2: Entraînement Local

```bash
# Prérequis
pip install -r backend/ml/requirements.txt

# Naviguer vers les modèles
cd backend/ml/models

# Entraîner un modèle
python train_model.py \
  --machine pompe \
  --dataset path/to/dataset.csv \
  --output trained/

# Fichiers générés:
# - pompe_xgb.pkl
# - pompe_scaler.pkl
# - pompe_label_encoder.pkl
# - pompe_metadata.json
```

---

## 📊 Datasets Recommandés

### Moteur Électrique

**Dataset**: CWRU Bearing Data Center  
**Source**: [Case Western Reserve University](https://engineering.case.edu/bearingdatacenter)  
**Kaggle**: `brjapon/cwru-bearing-datasets`  
**Taille**: ~50 MB  
**Classes**: Normal, Inner race fault, Outer race fault, Ball fault

```bash
kaggle datasets download -d brjapon/cwru-bearing-datasets --unzip
```

### Pompe Hydraulique

**Dataset**: Pump Sensor Data  
**Kaggle**: `nphantawee/pump-sensor-data`  
**Taille**: ~20 MB  
**Classes**: Normal, Cavitation, Mechanical seal wear

```bash
kaggle datasets download -d nphantawee/pump-sensor-data --unzip
```

### Compresseur d'Air

**Dataset**: Compressor Data  
**Kaggle**: `pythonkumar/compressor-data`  
**Taille**: ~15 MB  
**Classes**: Normal, Valve wear, Oil cooling issue

```bash
kaggle datasets download -d pythonkumar/compressor-data --unzip
```

### Échangeur Thermique

**Dataset**: Synthetic (généré)  
**Source**: Notebook inclus  
**Classes**: Normal, Fouling, Internal leak

Pas de téléchargement nécessaire, le notebook génère les données.

---

## 🔧 Configuration Kaggle API

### Étape 1: Obtenir Token

1. Aller sur https://www.kaggle.com/settings
2. Section "API" → "Create New API Token"
3. Télécharger `kaggle.json`

### Étape 2: Installer sur Windows

```powershell
# Créer dossier .kaggle
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.kaggle"

# Copier kaggle.json
Copy-Item "Downloads\kaggle.json" "$env:USERPROFILE\.kaggle\kaggle.json"

# Vérifier
Test-Path "$env:USERPROFILE\.kaggle\kaggle.json"
```

### Étape 3: Tester

```bash
# Installer CLI
pip install kaggle

# Tester connexion
kaggle datasets list -s "bearing"
```

---

## 🎨 Configuration Modèles

### Hyperparamètres XGBoost

```python
XGBClassifier(
    n_estimators=100,         # Nombre d'arbres
    max_depth=6,              # Profondeur max
    learning_rate=0.1,        # Taux d'apprentissage
    objective='multi:softprob',  # Classification multi-classe
    random_state=42,
    subsample=0.8,            # Échantillonnage
    colsample_bytree=0.8,     # Features sampling
)
```

### Normalisation

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

### Classes de Défauts

```python
# Moteur
DEFECT_CLASSES_MOTEUR = [
    'normal_operation',
    'degradation_roulement',
    'desequilibre_desalignement'
]

# Pompe
DEFECT_CLASSES_POMPE = [
    'normal_operation',
    'cavitation',
    'usure_garniture_mecanique'
]

# Compresseur
DEFECT_CLASSES_COMPRESSEUR = [
    'normal_operation',
    'usure_soupapes',
    'refroidissement_huile'
]

# Échangeur
DEFECT_CLASSES_ECHANGEUR = [
    'normal_operation',
    'encrassement_progressif',
    'fuite_interne'
]
```

---

## 🔬 Fine-Tuning avec Données Production

### Vue d'Ensemble

Le système **enregistre automatiquement** toutes les prédictions dans PostgreSQL pour permettre le fine-tuning.

### Workflow Fine-Tuning

```
Production → Prédictions Logged → Feedback Labels → Fine-Tuning Colab → Nouveaux Modèles
    ↓              ↓                      ↓                 ↓                  ↓
  API ML    prediction_log table   Via API/UI      Google Colab GPU    Hot-reload
```

### Étape 1: Collecter Feedback

```bash
# API pour ajouter feedback
curl -X POST http://localhost:5000/api/ml/feedback/predictions/123/feedback \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "actual_defect": "cavitation",
    "severity": "high",
    "notes": "Confirmé par inspection"
  }'
```

### Étape 2: Exporter Données

```bash
# Télécharger données d'entraînement
curl "http://localhost:5000/api/ml/feedback/export/training-data?machine=pompe&format=csv" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o training_data_pompe.csv
```

### Étape 3: Fine-Tuner dans Colab

1. Upload `backend/ml/models/notebooks/finetune_model_colab.ipynb`
2. Configurer:
```python
API_URL = "http://your-server.com"
API_TOKEN = "your-jwt-token"
MACHINE_TYPE = "pompe"
```
3. Run all cells
4. Télécharger nouveaux modèles

### Étape 4: Déployer

```bash
# Copier nouveaux fichiers
cp pompe_xgb.pkl backend/ml/models/trained/
cp pompe_scaler.pkl backend/ml/models/trained/
cp pompe_label_encoder.pkl backend/ml/models/trained/
cp pompe_metadata.json backend/ml/models/trained/

# Hot-reload (sans redémarrer!)
curl -X POST http://localhost:5000/api/ml/reload?machine=pompe \
  -H "Authorization: Bearer YOUR_TOKEN"

# Vérifier
curl http://localhost:5000/api/ml/reload/verify \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🧪 Tests et Validation

### Test API Prédiction

```bash
# Prédiction moteur
curl -X POST http://localhost:5000/api/ml/predict \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "machine": "moteur",
    "sensors": {
      "vibration": 1.5,
      "current": 14.2,
      "temperature": 85.5
    }
  }'

# Réponse attendue:
{
  "machine": "moteur",
  "defect": "degradation_roulement",
  "defect_score": 0.85,
  "confidence": 0.92,
  "defect_scores": {
    "normal_operation": 0.08,
    "degradation_roulement": 0.85,
    "desequilibre_desalignement": 0.07
  },
  "model_name": "XGBoost-moteur-v1",
  "timestamp": "2026-07-22T10:30:00"
}
```

### Test Docker Direct

```bash
docker-compose exec ml python -c "
from engines.real_engine import RealMLEngine

engine = RealMLEngine()

# Test moteur
result = engine.predict('moteur', {
    'vibration': 1.5,
    'current': 14.2
})

print(f'Défaut: {result[\"defect\"]}')
print(f'Confiance: {result[\"confidence\"]:.0%}')
print(f'Scores: {result[\"defect_scores\"]}')
"
```

### Vérifier Modèles Chargés

```bash
docker-compose exec ml python -c "
from services.ml_service import MLService

svc = MLService()
print('Mock mode:', svc.mock_ml)
print('Engine:', type(svc.engine).__name__)
print('Models loaded:', list(svc.engine.models.keys()))
"
```

**Attendu**:
```
Mock mode: False
Engine: RealMLEngine
Models loaded: ['moteur', 'pompe', 'compresseur', 'echangeur']
```

---

## 📈 Métriques et Monitoring

### Statistiques Prédictions

```sql
-- Total prédictions par machine
SELECT machine, COUNT(*) as total
FROM prediction_log
GROUP BY machine;

-- Prédictions avec feedback
SELECT 
  pl.machine,
  COUNT(*) as total,
  SUM(CASE WHEN pf.is_correct THEN 1 ELSE 0 END) as correct,
  ROUND(AVG(CASE WHEN pf.is_correct THEN 1.0 ELSE 0.0 END) * 100, 2) as accuracy
FROM prediction_log pl
LEFT JOIN prediction_feedback pf ON pl.id = pf.prediction_log_id
GROUP BY pl.machine;
```

### API Statistiques

```bash
curl http://localhost:5000/api/ml/feedback/statistics?machine=pompe \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Réponse**:
```json
{
  "machine": "pompe",
  "total_predictions": 1523,
  "labeled_predictions": 142,
  "accuracy": 89.4,
  "defects_distribution": {
    "normal_operation": 1205,
    "cavitation": 198,
    "usure_garniture_mecanique": 120
  }
}
```

---

## 🚨 Troubleshooting

### Modèles ne chargent pas

```bash
# Vérifier fichiers présents
docker-compose exec ml ls -la /app/models/trained/

# Doit contenir 16 fichiers (4 par machine):
# - {machine}_xgb.pkl
# - {machine}_scaler.pkl
# - {machine}_label_encoder.pkl
# - {machine}_metadata.json

# Voir logs d'erreur
docker-compose logs ml | grep ERROR
```

### Mode Mock activé par erreur

```bash
# Vérifier variable d'environnement
docker-compose exec ml env | grep MOCK_ML

# Doit afficher: MOCK_ML=false

# Si incorrect, modifier .env et redémarrer
docker-compose restart ml
```

### Accuracy faible après fine-tuning

- Collecter plus de données (minimum 100 samples)
- Inclure données d'entraînement originales
- Vérifier distribution des classes (équilibrée)
- Augmenter `n_estimators` dans XGBoost

### Erreur "Feature mismatch"

Le nombre de features doit correspondre entre entraînement et production.

```python
# Vérifier dans metadata.json
{
  "n_features": 18,
  "feature_names": ["vibration_max", "vibration_min", ...]
}

# Si différent, ré-entraîner le modèle avec mêmes features
```

---

## 📚 Ressources

### Documentation
- **XGBoost**: https://xgboost.readthedocs.io/
- **Scikit-learn**: https://scikit-learn.org/
- **Feature Engineering**: https://machinelearningmastery.com/

### Datasets
- **CWRU**: https://engineering.case.edu/bearingdatacenter
- **Kaggle**: https://www.kaggle.com/datasets

### Notebooks
- Tous dans `backend/ml/models/notebooks/`

---

## 🎯 Résumé Quick Start

```bash
# 1. Configuration Kaggle
# Télécharger kaggle.json depuis https://www.kaggle.com/settings

# 2. Copier dans .kaggle/
cp Downloads/kaggle.json ~/.kaggle/

# 3. Entraîner modèles (Google Colab)
# Upload notebooks vers https://colab.research.google.com/

# 4. Télécharger modèles entraînés

# 5. Copier dans projet
cp ~/Downloads/*_xgb.pkl backend/ml/models/trained/
cp ~/Downloads/*_scaler.pkl backend/ml/models/trained/
cp ~/Downloads/*_label_encoder.pkl backend/ml/models/trained/
cp ~/Downloads/*_metadata.json backend/ml/models/trained/

# 6. Redémarrer service
docker-compose restart ml

# 7. Vérifier
docker-compose exec ml python -c "from services.ml_service import MLService; print(list(MLService().engine.models.keys()))"
```

---

**Guide créé**: 22 Juillet 2026  
**Auteur**: Mohamed Sadok  
**Projet**: SmartMaintain
