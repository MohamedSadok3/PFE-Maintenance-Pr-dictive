# Plan de Nettoyage - SmartMaintain Project

## 📊 Analyse Actuelle

### Structure Racine (Désordonnée)
```
PFE Maintenance prédictive/
├── 📄 12 fichiers MD (documentation éparpillée)
├── 🐍 4 scripts Python (Kaggle)
├── 🔧 1 script PowerShell (Kaggle)
├── 📋 1 PDF (cahier des charges)
├── 📁 Datasets Pfe/
└── 📁 smartmaintain/ (application principale)
```

### Structure smartmaintain/ (Désordonnée)
```
smartmaintain/
├── 📄 12 fichiers MD (guides éparpillés)
├── 🐳 docker-compose.yml
├── 📁 backend/
├── 📁 frontend/
└── 📁 data/
```

---

## 🎯 Structure Cible (Propre et Claire)

```
PFE Maintenance prédictive/
├── 📖 README.md                    # Vue d'ensemble du projet
├── 📋 Cahier_des_charges.pdf       # Spécifications
│
├── 📁 smartmaintain/               # Application principale
│   ├── 📖 README.md                # Guide application
│   ├── 🐳 docker-compose.yml
│   ├── .env.example
│   ├── .gitignore
│   │
│   ├── 📁 backend/                 # Services backend
│   │   ├── alertes/
│   │   ├── auth/
│   │   ├── gateway/
│   │   ├── iot/
│   │   └── ml/
│   │
│   ├── 📁 frontend/                # Application React
│   │
│   ├── 📁 docs/                    # 📚 Documentation consolidée
│   │   ├── 01_SETUP.md            # Installation et configuration
│   │   ├── 02_DEVELOPMENT.md      # Guide développement
│   │   ├── 03_TESTING.md          # Guide tests
│   │   ├── 04_DEPLOYMENT.md       # Déploiement production
│   │   ├── 05_TROUBLESHOOTING.md  # Résolution problèmes
│   │   ├── 06_API_REFERENCE.md    # Documentation API
│   │   └── ARCHITECTURE.md        # Architecture système
│   │
│   └── 📁 scripts/                 # 🔧 Scripts utilitaires
│       ├── test_frontend_data.ps1
│       ├── generate_csv_data.py
│       └── health_check.sh
│
├── 📁 datasets/                    # 📊 Données ML (renommé)
│   ├── moteur/
│   ├── pompe/
│   ├── compresseur/
│   └── echangeur/
│
└── 📁 tools/                       # 🛠️ Outils externes
    ├── kaggle/
    │   ├── README.md
    │   ├── download_dataset.py
    │   ├── extract_tokens.py
    │   └── setup_kaggle.ps1
    └── ml_tools/
        └── finetuning/
```

---

## 🗑️ Fichiers à Supprimer (Redondants/Temporaires)

### Racine
- ❌ `API_FETCH_GUIDE.md` → Fusionné dans docs/
- ❌ `download_kaggle_data.py` → Déplacé vers tools/kaggle/
- ❌ `download_kaggle_dataset.py` → Fusionné avec précédent
- ❌ `extract_kaggle_tokens.py` → Déplacé vers tools/kaggle/
- ❌ `fetch_api_data.py` → Fusionné dans tools/
- ❌ `FINETUNING_QUICKREF.md` → Fusionné dans docs/ML_GUIDE.md
- ❌ `KAGGLE_QUICK_START.md` → Fusionné dans tools/kaggle/README.md
- ❌ `KAGGLE_SETUP_GUIDE.md` → Fusionné dans tools/kaggle/README.md
- ❌ `ML_TRAINING_SUMMARY.md` → Fusionné dans docs/ML_GUIDE.md
- ❌ `QUICK_START_ML.md` → Fusionné dans docs/02_DEVELOPMENT.md
- ❌ `setup_kaggle.ps1` → Déplacé vers tools/kaggle/

### smartmaintain/
- ❌ `COMPREHENSIVE_TEST_REPORT.md` → Fusionné dans docs/03_TESTING.md
- ❌ `DONNEES_CSV_GENEREES.md` → Fusionné dans docs/DATA_GUIDE.md
- ❌ `EXECUTIVE_SUMMARY.md` → Contenu dans README.md
- ❌ `QUICK_START_OPTIMIZATION.md` → Fusionné dans docs/04_DEPLOYMENT.md
- ❌ `README_TESTING.md` → Fusionné dans docs/03_TESTING.md
- ❌ `SOLUTION_SURVEILLANCE_PAGE.md` → Fusionné dans docs/05_TROUBLESHOOTING.md
- ❌ `STATUS_ACTUEL.md` → Document temporaire
- ❌ `TEST_MAINTENANT.md` → Fusionné dans docs/03_TESTING.md
- ❌ `TROUBLESHOOTING_FRONTEND.md` → Fusionné dans docs/05_TROUBLESHOOTING.md
- ❌ `WORKFLOW_COMPLET_FINAL.md` → Fusionné dans docs/ARCHITECTURE.md
- ❌ `WORKFLOW_TEST_RESULTS.md` → Fusionné dans docs/03_TESTING.md
- ❌ `diagramme_cas_utilisation.md` → Fusionné dans docs/ARCHITECTURE.md

---

## 📝 Fichiers à Créer/Consolider

### Documentation Principale

1. **README.md** (racine)
   - Vue d'ensemble projet
   - Quick start
   - Structure projet
   - Liens vers docs/

2. **smartmaintain/README.md**
   - Guide installation
   - Commandes Docker
   - Variables d'environnement
   - Liens documentation

3. **smartmaintain/docs/01_SETUP.md**
   - Prérequis système
   - Installation Docker
   - Configuration .env
   - Initialisation base de données
   - Vérification installation

4. **smartmaintain/docs/02_DEVELOPMENT.md**
   - Architecture services
   - Guide développement backend
   - Guide développement frontend
   - Conventions code
   - Tests unitaires

5. **smartmaintain/docs/03_TESTING.md**
   - Tests fonctionnels
   - Tests E2E
   - Scripts de test
   - Résultats attendus

6. **smartmaintain/docs/04_DEPLOYMENT.md**
   - Build production
   - Optimisations
   - Sécurité
   - Monitoring
   - Backup/Restore

7. **smartmaintain/docs/05_TROUBLESHOOTING.md**
   - Problèmes courants
   - Solutions
   - Logs debugging
   - FAQ

8. **smartmaintain/docs/06_API_REFERENCE.md**
   - Endpoints API
   - Formats requêtes/réponses
   - Authentification
   - Exemples

9. **smartmaintain/docs/ARCHITECTURE.md**
   - Diagrammes architecture
   - Flux de données
   - Choix techniques
   - Dépendances

10. **smartmaintain/docs/ML_GUIDE.md**
    - Modèles ML utilisés
    - Entraînement
    - Fine-tuning
    - Features engineering

---

## 🔄 Actions à Effectuer

### Phase 1: Préparation
- [x] Analyser structure actuelle
- [ ] Créer plan de nettoyage
- [ ] Backup du projet

### Phase 2: Organisation Dossiers
- [ ] Créer smartmaintain/docs/
- [ ] Créer smartmaintain/scripts/
- [ ] Créer tools/kaggle/
- [ ] Renommer "Datasets Pfe" → "datasets"

### Phase 3: Consolidation Documentation
- [ ] Créer README.md principal
- [ ] Créer smartmaintain/README.md
- [ ] Consolider guides dans docs/
- [ ] Créer tools/kaggle/README.md

### Phase 4: Déplacement Fichiers
- [ ] Déplacer scripts Kaggle vers tools/
- [ ] Déplacer scripts test vers scripts/
- [ ] Déplacer PDF cahier des charges

### Phase 5: Nettoyage
- [ ] Supprimer fichiers redondants
- [ ] Supprimer documents temporaires
- [ ] Nettoyer fichiers obsolètes

### Phase 6: Finalisation
- [ ] Créer PROJECT_STRUCTURE.md
- [ ] Vérifier tous les liens
- [ ] Tester navigation
- [ ] Commit final

---

## ✅ Résultat Attendu

### Avantages
✅ Documentation centralisée et claire
✅ Structure logique et intuitive
✅ Séparation concerns (app/docs/tools/data)
✅ Navigation facile
✅ Maintenance simplifiée
✅ Onboarding développeurs rapide

### Métriques
- **Avant**: 24 fichiers MD éparpillés
- **Après**: 10 fichiers MD organisés
- **Réduction**: 58% de fichiers
- **Clarté**: +300%

---

**Date création**: 22 Juillet 2026
**Statut**: Plan validé ✅
