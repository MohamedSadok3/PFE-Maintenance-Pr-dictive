# SmartMaintain - Plateforme de Maintenance Prédictive

**Version**: 1.0  
**Date**: 22 Juillet 2026  
**Statut**: Prototype PFE en cours de validation

---

## 🎯 Vue d'Ensemble

SmartMaintain est une **plateforme de maintenance prédictive** qui utilise le Machine Learning pour surveiller en temps réel la santé de machines industrielles et détecter les défauts avant qu'ils ne causent des pannes coûteuses.

### Machines Surveillées

- ⚙️ **Moteur électrique** - Détection roulements et désalignement
- 💧 **Pompe hydraulique** - Détection cavitation et usure joints  
- 🌀 **Compresseur d'air** - Détection usure soupapes et refroidissement
- 🔥 **Échangeur thermique** - Détection encrassement et fuites

### Technologies

```
Frontend:  React 18 + Vite + Recharts + Socket.IO
Backend:   Python Flask + XGBoost + PostgreSQL + Redis
DevOps:    Docker + Docker Compose
ML:        XGBoost (96-100% accuracy) + Feature Engineering
```

---

## 🚀 Quick Start (5 minutes)

### Prérequis

- Docker Desktop 20.10+
- 8 GB RAM minimum
- 20 GB espace disque

### Installation

```bash
# 1. Cloner le projet
git clone https://github.com/your-repo/smartmaintain.git
cd smartmaintain

# 2. Copier fichier environnement
cp .env.example .env

# 3. Lancer tous les services
docker-compose up -d

# 4. Attendre initialisation (30-60s)
timeout /t 60 /nobreak

# 5. Accéder à l'application
Start-Process "http://localhost:3000"
```

### Compte initial

Le compte superadministrateur est configuré dans `smartmaintain/.env` avec
`SUPERADMIN_EMAIL` et `SUPERADMIN_PASSWORD`. Utilisez des valeurs uniques avant
le premier démarrage; aucun identifiant de production n'est fourni dans Git.

---

## 📁 Structure du Projet

**Note**: l'application active se trouve dans `smartmaintain/`.

```
PFE Maintenance prédictive/
│
├── 📖 README.md                        # Ce fichier - Point d'entrée
├── 📄 CDC_SmartMaintain_avec_UML.docx  # Cahier des charges
├── 📄 LICENSE                          # Licence MIT
├── 📁 .git/                            # Git repository
├── 📄 .gitignore
│
├── 📁 smartmaintain/                   # 🚀 APPLICATION PRINCIPALE
│   ├── 📖 README.md                    # Guide rapide application
│   ├── 🐳 docker-compose.yml           # Orchestration services
│   ├── 🔒 .env / .env.example          # Configuration
│   ├── 📄 mosquitto.conf               # Config MQTT
│   │
│   ├── 📁 backend/                     # Services backend (5 microservices)
│   │   ├── gateway/                    # API Gateway + WebSocket (:5000)
│   │   ├── auth/                       # Authentification JWT (:5001)
│   │   ├── alertes/                    # Gestion alertes (:5002)
│   │   ├── ml/                         # Service ML XGBoost (:5003)
│   │   ├── iot/                        # Ingestion capteurs (:5004)
│   │   ├── shared/                     # Code partagé
│   │   ├── migrations/                 # Migrations base données
│   │   └── tests/                      # Tests automatisés
│   │
│   ├── 📁 frontend/                    # Application React
│   │   ├── src/
│   │   │   ├── pages/                  # LoginPage, DashboardPage, etc.
│   │   │   ├── components/             # Composants réutilisables
│   │   │   ├── hooks/                  # Custom React hooks
│   │   │   └── services/               # API & WebSocket
│   │   ├── public/                     # Assets statiques
│   │   └── package.json
│   │
│   ├── 📁 docs/                        # 📚 DOCUMENTATION CENTRALISÉE
│   │   ├── README.md                   # Index documentation
│   │   ├── 01_SETUP.md                 # Installation et configuration
│   │   ├── ARCHITECTURE.md             # Architecture système complète
│   │   ├── USE_CASES.md                # Cas d'utilisation UML
│   │   └── ML_GUIDE.md                 # Guide Machine Learning
│
├── 📁 datasets/                        # 📊 DATASETS MACHINE LEARNING
│   └── Datasets Mouteur electrique/    # Données moteur existantes
│
└── 📁 tools/                           # 🔧 OUTILS EXTERNES
    ├── README.md                       # Documentation outils
    └── kaggle/                         # Outils Kaggle API
        ├── README.md
        ├── setup_kaggle.ps1
        ├── download_kaggle_data.py
        ├── download_kaggle_dataset.py
        ├── extract_kaggle_tokens.py
        └── fetch_api_data.py
```

---

## 🎨 Fonctionnalités Principales

### 1. Dashboard Temps Réel

- Visualisation état global des machines
- Graphiques temps réel des capteurs
- Alertes prioritaires
- KPIs: disponibilité, MTBF, MTTR

### 2. Surveillance Machine

- Graphiques temps réel multi-capteurs (vibration, température, pression, etc.)
- Score défaut en temps réel (0-100%)
- Détection automatique anomalies
- Historique des défauts détectés
- Mode simulation si données indisponibles

### 3. Système d'Alertes

- Classification automatique sévérité (Normale → Critique)
- Notifications temps réel (WebSocket)
- Historique complet avec filtres
- Export rapports (PDF, CSV)
- Dédoublonnage intelligent

### 4. Gestion Utilisateurs & Plants

- Authentification JWT sécurisée
- Roles: Admin, Gestionnaire, Technicien
- Multi-plants support
- Gestion composants par usine
- Audit trail

---

## 🧠 Architecture ML

### Pipeline de Prédiction

```
Capteurs → Fenêtre glissante (20pts) → Features (9/capteur) → Normalisation → XGBoost → Classification
```

### Features Engineering

Pour chaque capteur, **9 features statistiques** calculées:
- max, min, mean, sd, rms
- skewness, kurtosis, crest_factor, form_factor

### Modèles Déployés

| Machine | Capteurs | Accuracy | Défauts Détectés |
|---------|----------|----------|------------------|
| Moteur | 2-3 | 100% | Roulement, Désalignement |
| Pompe | 3-4 | 100% | Cavitation, Usure joints |
| Compresseur | 4 | 96.5% | Usure soupapes, Refroidissement |
| Échangeur | 5 | 92.5% | Encrassement, Fuite |

---

## 🏗️ Architecture Système

### Services Docker

```yaml
┌─────────────────────────────────────────────┐
│  Frontend (React)          :3000            │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Gateway (Flask)           :5000            │
│  • Proxy HTTP                               │
│  • WebSocket Bridge                         │
│  • JWT Validation                           │
└──┬────────┬────────┬────────┬───────────────┘
   │        │        │        │
   ▼        ▼        ▼        ▼
┌──────┐ ┌─────┐ ┌──────┐ ┌───────┐
│ Auth │ │ IoT │ │  ML  │ │Alertes│
│ :5001│ │:5004│ │ :5003│ │ :5002 │
└──┬───┘ └──┬──┘ └──┬───┘ └───┬───┘
   │        │       │         │
   │        ▼       ▼         │
   │     ┌──────────────┐     │
   │     │ Redis :6379  │     │
   │     │ Pub/Sub      │     │
   │     └──────────────┘     │
   │                          │
   └──────────┬───────────────┘
              ▼
       ┌──────────────┐
       │PostgreSQL    │
       │ :5432        │
       └──────────────┘
```

### Flux de Données

```
CSV → IoT Service → Redis (sensor_data)
  → ML Service → Redis (ml_predictions)
  → Alertes Service → PostgreSQL + WebSocket
  → Gateway → Frontend (temps réel)
```

---

## 📊 Métriques Performance

| Métrique | Valeur | Statut |
|----------|--------|--------|
| Latence ML | <50ms | ✅ Excellent |
| Throughput | 2/s | ✅ Bon |
| WebSocket latency | <100ms | ✅ Excellent |
| DB query time | <100ms | ✅ Bon |
| Frontend bundle | 800KB | ✅ Optimal |
| Memory footprint | 200MB | ✅ Efficient |

---

## 📚 Documentation

### Guides Complets

- **[Installation](smartmaintain/docs/01_SETUP.md)** - Configuration et installation
- **[Machine Learning](smartmaintain/docs/ML_GUIDE.md)** - Entraînement modèles
- **[Architecture](smartmaintain/docs/ARCHITECTURE.md)** - Architecture technique

### Quick Links

- 🚀 [Guide Rapide](smartmaintain/README.md)
- 🐳 [Docker Setup](smartmaintain/docker-compose.yml)

---

## 🛠️ Développement

### Commandes Utiles

```bash
# Démarrer tous les services
docker-compose up -d

# Voir les logs
docker-compose logs -f [service-name]

# Redémarrer un service
docker-compose restart [service-name]

# Arrêter tout
docker-compose down

# Rebuild après modifications
docker-compose build [service-name]
docker-compose up -d [service-name]
```

### Tests

```bash
# Tests unitaires
docker-compose exec ml pytest

# Vérification frontend
cd frontend
npm run lint

# Tests de charge
cd tools
./load_test.sh
```

---

## 🔒 Sécurité

### Bonnes Pratiques

✅ Mots de passe hashés (bcrypt)  
✅ Authentification JWT  
✅ RBAC (Role-Based Access Control)  
✅ Validation inputs  
✅ CORS configuré  
⬜ Rate limiting à configurer au niveau du reverse proxy
⬜ HTTPS/TLS à configurer au déploiement

### Checklist Production

- [ ] Changer `POSTGRES_PASSWORD`
- [ ] Générer nouveau `JWT_SECRET_KEY`
- [ ] Configurer HTTPS
- [ ] Activer rate limiting
- [ ] Configurer firewall
- [ ] Setup backup automatique
- [ ] Activer monitoring

---

## 🤝 Contribution

### Workflow Git

```bash
# 1. Créer branche feature
git checkout -b feature/nom-feature

# 2. Faire modifications et commits
git add .
git commit -m "feat: description"

# 3. Pusher
git push origin feature/nom-feature

# 4. Créer Pull Request sur GitHub
```

### Conventions Code

- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ESLint, Prettier
- **Git**: Conventional Commits
- **Tests**: Coverage minimum 80%

---

## 📞 Support & Contact

### Documentation
- 📖 [Guide Complet](smartmaintain/docs/)
- 🐛 [Issues GitHub](https://github.com/your-repo/issues)

### Équipe
- **Auteur**: Mohamed Sadok
- **Email**: mohamed.sadok@example.com
- **Projet**: PFE Maintenance Prédictive
- **Année**: 2026

---

## 📄 License

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

---

## 🎓 Crédits

### Technologies Utilisées

- **Frontend**: React, Vite, Recharts, Socket.IO
- **Backend**: Flask, SQLAlchemy, Redis, PostgreSQL
- **ML**: XGBoost, Scikit-learn, NumPy, Pandas
- **DevOps**: Docker, Docker Compose

### Datasets

- **CWRU Bearing Dataset**: Case Western Reserve University
- **Pump Sensor Data**: Kaggle
- **Compressor Data**: Kaggle

---

## 🚀 Roadmap

### Version 1.1 (Q3 2026)
- [ ] Support MQTT en temps réel
- [ ] Dashboard analytics avancé
- [ ] Mobile app (React Native)
- [ ] Rapports automatiques PDF

### Version 2.0 (Q4 2026)
- [ ] Deep Learning (LSTM, CNN)
- [ ] Détection anomalies non-supervisée
- [ ] Multi-tenancy
- [ ] API publique REST

---

**Démarrez maintenant**: `cd smartmaintain && docker-compose up -d` 🚀

**Documentation**: [smartmaintain/docs/](smartmaintain/docs/)

**Status**: Prototype PFE — validation d'intégration et durcissement requis avant production
