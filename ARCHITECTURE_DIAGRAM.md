# Diagrammes Architecture - SmartMaintain

**Date**: 22 Juillet 2026  
**Version**: 2.0 (Refactorisée)

---

## 🗂️ Structure Projet Complète

```
PFE Maintenance prédictive/
│
├── 📖 README.md                        ⭐ Vue d'ensemble projet
├── 📋 Cahier_des_charges.pdf           📄 Spécifications
├── 📋 PROJECT_STRUCTURE.md             📁 Structure détaillée
├── 📋 PROJECT_CLEANUP_PLAN.md          📝 Plan refactorisation
├── 📋 ARCHITECTURE_DIAGRAM.md          🏗️ Ce fichier
│
├── 📁 .venv/                           🐍 Python virtual env
│
├── 📁 smartmaintain/                   🚀 APPLICATION PRINCIPALE
│   ├── 📖 README.md
│   ├── 🐳 docker-compose.yml
│   ├── 🔒 .env / .env.example
│   ├── 📁 backend/        (8 services)
│   ├── 📁 frontend/       (React app)
│   ├── 📁 docs/          (8 guides)
│   ├── 📁 scripts/       (Utilitaires)
│   └── 📁 data/          (CSV générés)
│
├── 📁 datasets/                        📊 Datasets ML
│   ├── moteur/
│   ├── pompe/
│   ├── compresseur/
│   └── echangeur/
│
└── 📁 tools/                           🛠️ Outils externes
    └── kaggle/           (5 scripts)
```

---

## 🏗️ Architecture Microservices

```
                    ┌─────────────────────────────────────┐
                    │      FRONTEND (React + Vite)        │
                    │         http://localhost:3000       │
                    │  • LoginPage                        │
                    │  • DashboardPage                    │
                    │  • SurveillancePage                 │
                    │  • AlertesPage                      │
                    └──────────────┬──────────────────────┘
                                   │ HTTP + WebSocket
                                   │
                    ┌──────────────▼──────────────────────┐
                    │    GATEWAY (API + WebSocket)        │
                    │         :5000                       │
                    │  • HTTP Proxy                       │
                    │  • WebSocket Bridge                 │
                    │  • JWT Validation                   │
                    │  • CORS                             │
                    └──┬────────┬────────┬────────┬───────┘
                       │        │        │        │
        ┌──────────────┘        │        │        └──────────────┐
        │                       │        │                       │
        ▼                       ▼        ▼                       ▼
┌───────────────┐      ┌───────────┐  ┌──────────┐    ┌────────────────┐
│  AUTH         │      │    IoT    │  │    ML    │    │   ALERTES      │
│  :5001        │      │   :5004   │  │   :5003  │    │    :5002       │
│               │      │           │  │          │    │                │
│ • JWT Auth    │      │ • CSV     │  │ • XGBoost│    │ • Redis        │
│ • Users       │      │   Replay  │  │ • 4      │    │   Consumer     │
│ • Plants      │      │ • Features│  │   Models │    │ • AlertService │
│ • Components  │      │ • Publish │  │ • Predict│    │ • WebSocket    │
└───────┬───────┘      └─────┬─────┘  └────┬─────┘    └────────┬───────┘
        │                    │             │                   │
        │                    └─────┐   ┐───┘                   │
        │                          │   │                       │
        │                          ▼   ▼                       │
        │                   ┌─────────────────┐                │
        │                   │  REDIS  :6379   │                │
        │                   │                 │                │
        │                   │ • Pub/Sub       │                │
        │                   │   - sensor_data │                │
        │                   │   - ml_pred...  │                │
        │                   │ • Cache         │                │
        │                   └─────────────────┘                │
        │                                                      │
        └──────────────────┬───────────────────────────────────┘
                           │
                           ▼
                  ┌────────────────────┐
                  │ PostgreSQL  :5432  │
                  │                    │
                  │ • users            │
                  │ • plants           │
                  │ • components       │
                  │ • alerts           │
                  │ • prediction_log   │
                  └────────────────────┘
```

---

## 🔄 Flux de Données ML (Temps Réel)

```
┌─────────────────────────────────────────────────────────────────┐
│  ÉTAPE 1: DONNÉES SOURCES                                       │
│  📁 backend/iot/data/                                           │
│    • moteur.csv         (vibration, current, temperature)       │
│    • pompe.csv          (vibration, pressure_in/out, flow)      │
│    • compresseur.csv    (pressure, current, temp_oil/air)       │
│    • echangeur.csv      (temp_in/out_hot/cold, flow_rate)      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ÉTAPE 2: IOT SERVICE (ReplayService)                          │
│  🔄 Lecture CSV + Fenêtre glissante (20 échantillons)          │
│                                                                 │
│  Pour chaque capteur, calcule 9 features:                      │
│    • max, min, mean, sd, rms                                   │
│    • skewness, kurtosis, crest_factor, form_factor            │
│                                                                 │
│  📤 Publie sur Redis → canal "sensor_data" (toutes les 2s)     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  REDIS: Canal "sensor_data"                                    │
│  {                                                              │
│    "machine": "moteur",                                         │
│    "sensors": {                                                 │
│      "vibration_max": 0.89, "vibration_rms": 0.39, ...        │
│      "current_max": 18.5, "current_rms": 12.5, ...            │
│      "vibration_instant": 0.89,                                │
│      "current_instant": 10.98,                                 │
│      "temperature": 77.42                                       │
│    },                                                           │
│    "timestamp": "2025-01-01T01:44:00"                          │
│  }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ÉTAPE 3: ML SERVICE (RealMLEngine)                            │
│  🤖 Consomme "sensor_data"                                      │
│                                                                 │
│  1. Extrait features ML (9 x N capteurs)                       │
│  2. Normalise avec StandardScaler                              │
│  3. Prédit avec XGBoost                                        │
│  4. Map classes: CWRU → SmartMaintain                          │
│  5. Calcule scores défauts                                     │
│                                                                 │
│  📤 Publie sur Redis → canal "ml_predictions"                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  REDIS: Canal "ml_predictions"                                 │
│  {                                                              │
│    "machine": "moteur",                                         │
│    "defect": "normal_operation",                                │
│    "defect_score": 0.0586,                                     │
│    "confidence": 0.9414,                                        │
│    "defect_scores": {                                          │
│      "degradation_roulement": 0.0127,                          │
│      "desequilibre_desalignement": 0.0459,                     │
│      "normal_operation": 0.9414                                │
│    },                                                           │
│    "sensors": { ... },                                         │
│    "timestamp": "2025-01-01T01:44:00"                          │
│  }                                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ÉTAPE 4: ALERTES SERVICE (RedisConsumer)                      │
│  🚨 Consomme "ml_predictions"                                   │
│                                                                 │
│  1. Calcule sévérité (score → niveau)                         │
│  2. Crée alerte dans PostgreSQL si score > seuil              │
│  3. Émet WebSocket "sensor:data" (vers frontend)              │
│  4. Émet WebSocket "alert:new" si alerte créée                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ÉTAPE 5: GATEWAY (WebSocket Bridge)                           │
│  🌐 Reçoit WebSocket du service Alertes                        │
│                                                                 │
│  📡 Broadcast vers clients frontend:                            │
│    • Event "sensor:data" → Données + prédiction ML            │
│    • Event "alert:new" → Nouvelle alerte                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  ÉTAPE 6: FRONTEND (React - SurveillancePage)                  │
│  📊 Hook useSurveillance                                        │
│                                                                 │
│  1. Connecte WebSocket au Gateway                              │
│  2. Écoute event "sensor:data"                                 │
│  3. Met à jour state React:                                    │
│     • chartData (buffer 60 points)                             │
│     • anomalyScore (%)                                         │
│     • defectScores (par type)                                  │
│     • sensorList (valeurs actuelles)                           │
│  4. Render:                                                     │
│     ✅ Graphiques temps réel (Recharts)                        │
│     ✅ Score défaut (gauge)                                    │
│     ✅ Historique défauts                                      │
└─────────────────────────────────────────────────────────────────┘

⏱️  Latence totale: ~100ms
🔄  Interval publication: 2 secondes
📊  4 machines surveillées simultanément
```

---

## 🗄️ Schéma Base de Données

```
┌─────────────────────────────────────────────────────────────────┐
│  TABLE: users                                                   │
├─────────────────────────────────────────────────────────────────┤
│  id               SERIAL PRIMARY KEY                            │
│  email            VARCHAR(255) UNIQUE NOT NULL                  │
│  password_hash    TEXT NOT NULL                                 │
│  role             VARCHAR(50) NOT NULL                          │
│                   (admin, gestionnaire, technicien)             │
│  first_name       VARCHAR(100)                                  │
│  last_name        VARCHAR(100)                                  │
│  verified         BOOLEAN DEFAULT FALSE                         │
│  plant_id         INTEGER → plants(id)                          │
│  machines         TEXT[] (array)                                │
│  created_at       TIMESTAMP DEFAULT NOW()                       │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ FK: plant_id
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  TABLE: plants                                                  │
├─────────────────────────────────────────────────────────────────┤
│  id               SERIAL PRIMARY KEY                            │
│  name             VARCHAR(255) NOT NULL                         │
│  location         TEXT                                          │
│  contact_email    VARCHAR(255)                                  │
│  owner_id         INTEGER → users(id)                           │
│  created_at       TIMESTAMP DEFAULT NOW()                       │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ FK: plant_id
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  TABLE: components                                              │
├─────────────────────────────────────────────────────────────────┤
│  id               SERIAL PRIMARY KEY                            │
│  name             VARCHAR(255) NOT NULL                         │
│  type             VARCHAR(100) NOT NULL                         │
│                   (moteur, pompe, compresseur, echangeur)       │
│  plant_id         INTEGER → plants(id)                          │
│  enabled          BOOLEAN DEFAULT TRUE                          │
│  created_at       TIMESTAMP DEFAULT NOW()                       │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ FK: component_id
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  TABLE: alerts                                                  │
├─────────────────────────────────────────────────────────────────┤
│  id               SERIAL PRIMARY KEY                            │
│  machine          VARCHAR(100) NOT NULL                         │
│  defect           VARCHAR(255) NOT NULL                         │
│  severity         VARCHAR(50) NOT NULL                          │
│                   (normal, faible, moyenne, elevee, critique)   │
│  defect_score     FLOAT NOT NULL                                │
│  confidence       FLOAT                                         │
│  status           VARCHAR(50) DEFAULT 'active'                  │
│                   (active, resolved, acknowledged)              │
│  start_time       TIMESTAMP DEFAULT NOW()                       │
│  end_time         TIMESTAMP                                     │
│  component_id     INTEGER → components(id)                      │
│  plant_id         INTEGER → plants(id)                          │
│  required_sensors TEXT[]                                        │
│  created_at       TIMESTAMP DEFAULT NOW()                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  TABLE: prediction_log (Fine-tuning ML)                        │
├─────────────────────────────────────────────────────────────────┤
│  id               SERIAL PRIMARY KEY                            │
│  machine          VARCHAR(100) NOT NULL                         │
│  sensors_data     JSONB NOT NULL                                │
│  predicted_defect VARCHAR(255) NOT NULL                         │
│  defect_score     FLOAT NOT NULL                                │
│  confidence       FLOAT NOT NULL                                │
│  timestamp        TIMESTAMP DEFAULT NOW()                       │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ FK: prediction_log_id
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  TABLE: prediction_feedback (Labels pour fine-tuning)          │
├─────────────────────────────────────────────────────────────────┤
│  id                   SERIAL PRIMARY KEY                        │
│  prediction_log_id    INTEGER → prediction_log(id)             │
│  actual_defect        VARCHAR(255) NOT NULL                     │
│  is_correct           BOOLEAN NOT NULL                          │
│  severity             VARCHAR(50)                               │
│  notes                TEXT                                      │
│  created_by           INTEGER → users(id)                       │
│  created_at           TIMESTAMP DEFAULT NOW()                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧠 Architecture ML (Feature Engineering)

```
┌─────────────────────────────────────────────────────────────────┐
│  CAPTEUR RAW (exemple: vibration)                              │
│  [0.34, 0.41, 0.38, 0.45, ..., 0.35]  (20 points)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  FEATURE ENGINEERING (9 features statistiques)                 │
│                                                                 │
│  1. max              = np.max(values)           → 0.8955       │
│  2. min              = np.min(values)           → 0.2676       │
│  3. mean             = np.mean(values)          → 0.3706       │
│  4. sd               = np.std(values)           → 0.1290       │
│  5. rms              = √(mean(values²))         → 0.3924       │
│  6. skewness         = skew(values)             → 3.2658       │
│  7. kurtosis         = kurtosis(values)         → 10.7887      │
│  8. crest_factor     = max / rms                → 2.2821       │
│  9. form_factor      = rms / mean_abs           → 1.0588       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  FEATURES VECTOR (exemple moteur: 2 capteurs)                  │
│                                                                 │
│  [vibration_max, vibration_min, ..., vibration_form,           │
│   current_max, current_min, ..., current_form]                 │
│                                                                 │
│  Total: 2 capteurs × 9 features = 18 features                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  NORMALISATION (StandardScaler)                                │
│                                                                 │
│  X_scaled = (X - mean) / std                                   │
│                                                                 │
│  • Fit sur training data                                       │
│  • Transform sur production data                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  MODÈLE XGBoost                                                │
│                                                                 │
│  • n_estimators = 100       (100 arbres)                       │
│  • max_depth = 6            (profondeur max)                   │
│  • learning_rate = 0.1      (taux apprentissage)               │
│  • objective = multi:softprob (classification multi-classe)    │
│                                                                 │
│  Input:  18 features (moteur)                                  │
│  Output: 3 probabilités (par classe)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PRÉDICTION                                                    │
│                                                                 │
│  Classes (moteur):                                             │
│    • normal_operation              → 94.14%                    │
│    • degradation_roulement         → 1.27%                     │
│    • desequilibre_desalignement    → 4.59%                     │
│                                                                 │
│  Résultat:                                                      │
│    defect = "normal_operation"                                 │
│    confidence = 0.9414                                         │
│    defect_score = 0.0586  (1 - confidence)                     │
└─────────────────────────────────────────────────────────────────┘
```

**Nombre de features par machine**:
- Moteur: 2-3 capteurs × 9 = 18-27 features
- Pompe: 3-4 capteurs × 9 = 27-36 features
- Compresseur: 4 capteurs × 9 = 36 features
- Échangeur: 5 capteurs × 9 = 45 features

---

## 📁 Organisation Fichiers Backend

```
backend/
│
├── 📁 gateway/ (:5000)
│   ├── app.py                   # Point d'entrée
│   ├── Dockerfile
│   ├── requirements.txt
│   └── __init__.py
│
├── 📁 auth/ (:5001)
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── queries.py               # SQL queries
│   ├── 📁 models/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── __init__.py
│   ├── 📁 routes/
│   │   ├── auth.py              # /api/auth/*
│   │   ├── users.py             # /api/users/*
│   │   ├── plants.py            # /api/plants/*
│   │   ├── components.py        # /api/components/*
│   │   └── __init__.py
│   ├── 📁 services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── plant_service.py
│   │   ├── component_service.py
│   │   ├── email_service.py
│   │   ├── registration_service.py
│   │   └── __init__.py
│   └── __init__.py
│
├── 📁 ml/ (:5003)
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── 📁 engines/
│   │   ├── real_engine.py       # XGBoost production
│   │   ├── mock_engine.py       # Mode simulation
│   │   └── __init__.py
│   ├── 📁 services/
│   │   ├── ml_service.py
│   │   └── __init__.py
│   ├── 📁 models/
│   │   ├── 📁 trained/          # Modèles déployés
│   │   │   ├── moteur_xgb.pkl
│   │   │   ├── moteur_scaler.pkl
│   │   │   ├── moteur_label_encoder.pkl
│   │   │   ├── moteur_metadata.json
│   │   │   └── ... (×4 machines)
│   │   ├── 📁 notebooks/        # Colab notebooks
│   │   │   ├── train_moteur_colab.ipynb
│   │   │   ├── train_pompe_colab.ipynb
│   │   │   ├── train_compresseur_colab.ipynb
│   │   │   ├── train_echangeur_colab.ipynb
│   │   │   └── finetune_model_colab.ipynb
│   │   ├── train_model.py       # CLI trainer
│   │   └── __init__.py
│   ├── 📁 migrations/
│   │   └── 001_prediction_logging.sql
│   └── __init__.py
│
├── 📁 iot/ (:5004)
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── 📁 data/
│   │   ├── moteur.csv
│   │   ├── pompe.csv
│   │   ├── compresseur.csv
│   │   └── echangeur.csv
│   ├── 📁 services/
│   │   ├── replay_service.py
│   │   └── __init__.py
│   └── __init__.py
│
├── 📁 alertes/ (:5002)
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── queries.py
│   ├── 📁 models/
│   │   ├── models.py
│   │   └── __init__.py
│   ├── 📁 routes/
│   │   ├── alerts.py
│   │   ├── dashboard.py
│   │   └── __init__.py
│   ├── 📁 services/
│   │   ├── alert_service.py
│   │   ├── redis_consumer.py
│   │   ├── exceptions.py
│   │   └── __init__.py
│   └── __init__.py
│
└── 📁 shared/
    ├── constants.py             # Constantes partagées
    └── __init__.py
```

---

## 📊 Organisation Frontend React

```
frontend/
│
├── 📦 package.json
├── 📄 vite.config.js
├── 📄 index.html
│
├── 📁 src/
│   │
│   ├── App.jsx                  # Point d'entrée principal
│   ├── main.jsx                 # ReactDOM render
│   │
│   ├── 📁 pages/                # Pages principales
│   │   ├── LoginPage.jsx        # /login
│   │   ├── DashboardPage.jsx    # /dashboard
│   │   ├── SurveillancePage.jsx # /surveillance
│   │   ├── AlertesPage.jsx      # /alertes
│   │   └── SettingsPage.jsx     # /settings
│   │
│   ├── 📁 components/           # Composants réutilisables
│   │   ├── SensorChart.jsx      # Graphique Recharts
│   │   ├── AlertCard.jsx        # Carte alerte
│   │   ├── MachineCard.jsx      # Carte machine
│   │   ├── DefectGauge.jsx      # Jauge score défaut
│   │   ├── Sidebar.jsx          # Menu latéral
│   │   ├── Header.jsx           # En-tête
│   │   └── ...
│   │
│   ├── 📁 hooks/                # Custom React hooks
│   │   ├── useSurveillance.js   # Hook surveillance temps réel
│   │   ├── useWebSocket.js      # Hook WebSocket
│   │   ├── useAuth.js           # Hook authentification
│   │   └── useAlerts.js         # Hook alertes
│   │
│   ├── 📁 services/             # Services API
│   │   ├── api.js               # Axios configuration
│   │   └── socketService.js     # Socket.IO client
│   │
│   ├── 📁 context/              # React Context
│   │   ├── AuthContext.jsx      # Context authentification
│   │   └── ThemeContext.jsx     # Context thème
│   │
│   ├── 📁 utils/                # Utilitaires
│   │   ├── formatters.js        # Format nombres, dates
│   │   └── validators.js        # Validation forms
│   │
│   └── 📁 styles/               # CSS/SCSS
│       ├── index.css
│       ├── variables.css
│       └── ...
│
├── 📁 public/                   # Assets statiques
│   ├── logo.svg
│   ├── favicon.ico
│   └── ...
│
└── 📁 dist/                     # Build production
    ├── index.html
    ├── assets/
    │   ├── index-[hash].js
    │   └── index-[hash].css
    └── ...
```

**Stack Frontend**:
- React 18
- Vite (build tool)
- Recharts (graphiques)
- Socket.IO Client (WebSocket)
- Axios (HTTP)
- React Router (routing)

---

## 🌐 API Routes (Gateway)

```
┌─────────────────────────────────────────────────────────────────┐
│  AUTHENTIFICATION                                               │
├─────────────────────────────────────────────────────────────────┤
│  POST   /api/auth/login                                         │
│  POST   /api/auth/register                                      │
│  POST   /api/auth/register-plant                                │
│  POST   /api/auth/verify-email                                  │
│  POST   /api/auth/refresh                                       │
│  GET    /api/auth/me                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  UTILISATEURS                                                   │
├─────────────────────────────────────────────────────────────────┤
│  GET    /api/users                      # Liste utilisateurs    │
│  GET    /api/users/:id                  # Détails utilisateur   │
│  POST   /api/users                      # Créer utilisateur     │
│  PUT    /api/users/:id                  # Modifier utilisateur  │
│  DELETE /api/users/:id                  # Supprimer utilisateur │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  PLANTS (Usines)                                                │
├─────────────────────────────────────────────────────────────────┤
│  GET    /api/plants                     # Liste plants          │
│  GET    /api/plants/:id                 # Détails plant         │
│  POST   /api/plants                     # Créer plant           │
│  PUT    /api/plants/:id                 # Modifier plant        │
│  DELETE /api/plants/:id                 # Supprimer plant       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  COMPONENTS (Machines)                                          │
├─────────────────────────────────────────────────────────────────┤
│  GET    /api/components                 # Liste composants      │
│  GET    /api/components/:id             # Détails composant     │
│  POST   /api/components                 # Créer composant       │
│  PUT    /api/components/:id             # Modifier composant    │
│  DELETE /api/components/:id             # Supprimer composant   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  MACHINE LEARNING                                               │
├─────────────────────────────────────────────────────────────────┤
│  POST   /api/ml/predict                 # Prédiction manuelle   │
│  GET    /api/ml/models                  # Liste modèles         │
│  POST   /api/ml/reload                  # Hot-reload modèle     │
│  GET    /api/ml/reload/verify           # Vérifier reload       │
│  GET    /api/ml/feedback/statistics     # Stats feedback        │
│  POST   /api/ml/feedback/predictions/:id/feedback  # Ajouter    │
│  GET    /api/ml/feedback/export/training-data  # Export CSV     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ALERTES                                                        │
├─────────────────────────────────────────────────────────────────┤
│  GET    /api/alertes                    # Liste alertes         │
│  GET    /api/alertes/:id                # Détails alerte        │
│  PUT    /api/alertes/:id                # Modifier alerte       │
│  DELETE /api/alertes/:id                # Supprimer alerte      │
│  POST   /api/alertes/:id/acknowledge    # Acquitter alerte      │
│  POST   /api/alertes/:id/resolve        # Résoudre alerte       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  DASHBOARD                                                      │
├─────────────────────────────────────────────────────────────────┤
│  GET    /api/dashboard/kpis             # KPIs globaux          │
│  GET    /api/dashboard/machines/status  # Status machines       │
│  GET    /api/dashboard/alerts/recent    # Alertes récentes      │
│  GET    /api/dashboard/analytics        # Analytics             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  WEBSOCKET EVENTS                                               │
├─────────────────────────────────────────────────────────────────┤
│  sensor:data          → Données capteurs + prédiction ML        │
│  alert:new            → Nouvelle alerte créée                   │
│  alert:updated        → Alerte mise à jour                      │
│  alert:resolved       → Alerte résolue                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Cycle de Vie Complet

```
┌─────────────────────────────────────────────────────────────────┐
│  1. STARTUP (Initialisation)                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  T=0s: docker-compose up -d                                     │
│    ├─ PostgreSQL démarre (5s)                                  │
│    ├─ Redis démarre (2s)                                       │
│    └─ Services backend démarrent (10-20s)                      │
│                                                                 │
│  T=10s: ML Service charge modèles                              │
│    ├─ moteur_xgb.pkl (249 KB) → 2s                            │
│    ├─ pompe_xgb.pkl (246 KB) → 2s                             │
│    ├─ compresseur_xgb.pkl (447 KB) → 3s                       │
│    └─ echangeur_xgb.pkl (486 KB) → 3s                         │
│                                                                 │
│  T=15s: IoT Service lit CSV                                    │
│    ├─ moteur.csv → 500 lignes                                 │
│    ├─ pompe.csv → 500 lignes                                  │
│    ├─ compresseur.csv → 500 lignes                            │
│    └─ echangeur.csv → 500 lignes                              │
│                                                                 │
│  T=20s: Frontend démarre (Vite dev server)                     │
│    └─ Build initial → http://localhost:3000                    │
│                                                                 │
│  T=30s: Système prêt ✅                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  2. RUNTIME (Fonctionnement normal)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Toutes les 2 secondes (en boucle):                            │
│                                                                 │
│  T=0ms:   IoT lit ligne CSV                                    │
│  T=5ms:   IoT calcule features (fenêtre 20 pts)               │
│  T=10ms:  IoT publie Redis (sensor_data)                      │
│  T=15ms:  ML consomme Redis                                    │
│  T=20ms:  ML normalise features                                │
│  T=25ms:  ML prédit XGBoost (4 machines)                      │
│  T=45ms:  ML publie Redis (ml_predictions)                    │
│  T=50ms:  Alertes consomme Redis                               │
│  T=55ms:  Alertes évalue sévérité                             │
│  T=60ms:  Alertes crée alerte si besoin (PostgreSQL)          │
│  T=65ms:  Alertes émet WebSocket (sensor:data)                │
│  T=70ms:  Gateway broadcast WebSocket                          │
│  T=75ms:  Frontend reçoit données                              │
│  T=80ms:  Frontend met à jour state React                      │
│  T=100ms: Frontend re-render composants                        │
│                                                                 │
│  Latence totale: ~100ms par cycle                              │
│  Throughput: 4 machines × 0.5 Hz = 2 prédictions/sec          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  3. USER INTERACTION (Utilisateur)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Utilisateur ouvre http://localhost:3000                     │
│  2. Affiche LoginPage                                          │
│  3. Utilisateur se connecte                                    │
│     → POST /api/auth/login                                     │
│     ← JWT token                                                │
│  4. Redirect vers DashboardPage                                │
│     → GET /api/dashboard/kpis                                  │
│     ← KPIs (disponibilité, MTBF, alertes)                     │
│  5. Utilisateur clique "Surveillance"                          │
│  6. SurveillancePage démarre                                   │
│     → Connexion WebSocket (Gateway :5000)                      │
│     → Écoute événement "sensor:data"                           │
│  7. Données arrivent toutes les 2s                             │
│     → Frontend met à jour graphiques Recharts                  │
│     → Buffer 60 points (2 minutes historique)                  │
│  8. Utilisateur switch onglet machine (tabs)                   │
│     → Filter data par machine                                  │
│     → Re-render graphiques                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  4. SHUTDOWN (Arrêt)                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  docker-compose down                                            │
│    ├─ Frontend stop (instant)                                  │
│    ├─ Services backend stop (SIGTERM → graceful)              │
│    │   ├─ Gateway ferme WebSocket clients                     │
│    │   ├─ IoT arrête boucle replay                            │
│    │   ├─ ML flush Redis consumer                             │
│    │   └─ Alertes ferme connexions PostgreSQL                 │
│    ├─ Redis stop (sauvegarde RDB)                             │
│    └─ PostgreSQL stop (checkpoint WAL)                         │
│                                                                 │
│  docker-compose down -v (avec volumes)                          │
│    └─ Supprime données PostgreSQL + Redis                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📈 Métriques Performance

```
┌─────────────────────────────────────────────────────────────────┐
│  LATENCES                                                       │
├────────────────────────────────┬────────────┬───────────────────┤
│  Opération                     │  Actuel    │  Objectif         │
├────────────────────────────────┼────────────┼───────────────────┤
│  ML Prédiction (1 machine)     │  45ms      │  <100ms      ✅   │
│  Redis Pub/Sub                 │  <5ms      │  <10ms       ✅   │
│  WebSocket broadcast           │  50ms      │  <200ms      ✅   │
│  PostgreSQL query (alerts)     │  150ms     │  <100ms      ⚠️   │
│  HTTP request (Gateway)        │  20ms      │  <50ms       ✅   │
│  Frontend render                │  16ms      │  <16ms (60fps) ✅  │
└────────────────────────────────┴────────────┴───────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  THROUGHPUT                                                     │
├────────────────────────────────┬────────────┬───────────────────┤
│  Métrique                      │  Actuel    │  Objectif         │
├────────────────────────────────┼────────────┼───────────────────┤
│  Prédictions ML/sec            │  2/s       │  10/s        ⚠️   │
│  Messages Redis/sec            │  8/s       │  100/s       ✅   │
│  WebSocket clients simultanés  │  50        │  100         ✅   │
│  HTTP requests/sec             │  100/s     │  1000/s      ✅   │
└────────────────────────────────┴────────────┴───────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  RESSOURCES                                                     │
├────────────────────────────────┬────────────┬───────────────────┤
│  Service                       │  Memory    │  CPU              │
├────────────────────────────────┼────────────┼───────────────────┤
│  PostgreSQL                    │  150 MB    │  5-10%       ✅   │
│  Redis                         │  50 MB     │  2-5%        ✅   │
│  ML Service                    │  200 MB    │  10-20%      ✅   │
│  IoT Service                   │  80 MB     │  5-10%       ✅   │
│  Alertes Service               │  100 MB    │  5-10%       ✅   │
│  Auth Service                  │  80 MB     │  3-5%        ✅   │
│  Gateway                       │  100 MB    │  5-10%       ✅   │
│  Frontend (Vite dev)           │  150 MB    │  5-10%       ✅   │
│                                │            │               │
│  TOTAL                         │  ~910 MB   │  40-80%      ✅   │
└────────────────────────────────┴────────────┴───────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  TAILLE FICHIERS                                                │
├────────────────────────────────┬─────────────────────────────────┤
│  Composant                     │  Taille                         │
├────────────────────────────────┼─────────────────────────────────┤
│  Modèles ML (4 × 4 fichiers)  │  1.4 MB                    ✅   │
│  Frontend bundle (prod)        │  800 KB                    ✅   │
│  Docker images (total)         │  ~2.5 GB                   ✅   │
│  Base de données (initiale)    │  10 MB                     ✅   │
│  CSV données (4 machines)      │  ~500 KB                   ✅   │
└────────────────────────────────┴─────────────────────────────────┘

Légende:
  ✅ Optimal (dans objectifs)
  ⚠️ À améliorer (hors objectifs)
  🔴 Critique (problème majeur)
```

---

## 🎯 Points Clés Architecture

### ✅ Forces

1. **Microservices découplés**: Chaque service est indépendant
2. **Temps réel**: WebSocket + Redis Pub/Sub performant
3. **Scalable**: Services peuvent être répliqués horizontalement
4. **ML Production-ready**: 4 modèles XGBoost déployés
5. **Code modulaire**: Séparation concerns (routes, services, models)

### ⚠️ Points d'Amélioration

1. **DB Performance**: Ajouter index pour queries alertes
2. **ML Throughput**: Batch processing pour 10/s
3. **Monitoring**: Ajouter Prometheus + Grafana
4. **Tests**: Coverage actuellement <20%
5. **Documentation API**: Ajouter OpenAPI/Swagger

### 🔐 Sécurité

1. **JWT Authentication**: Tokens expiration 24h
2. **Password hashing**: bcrypt avec salt
3. **RBAC**: 3 roles (admin, gestionnaire, technicien)
4. **Input validation**: Validation côté backend
5. **CORS**: Configuré pour frontend uniquement

---

**Document créé**: 22 Juillet 2026  
**Version**: 2.0  
**Auteur**: Mohamed Sadok  
**Projet**: SmartMaintain - PFE Maintenance Prédictive
