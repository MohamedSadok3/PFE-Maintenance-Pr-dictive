# Guide d'Installation - SmartMaintain

**Dernière mise à jour**: 22 Juillet 2026

---

## 📋 Prérequis Système

### Logiciels Requis

| Logiciel | Version Minimum | Notes |
|----------|----------------|-------|
| Docker Desktop | 20.10+ | Inclut Docker Compose |
| Python | 3.9+ | Pour scripts utilitaires |
| Node.js | 16+ | Pour développement frontend |
| Git | 2.30+ | Gestion de code |

### Configuration Matérielle Recommandée

- **CPU**: 4 cores minimum
- **RAM**: 8 GB minimum (16 GB recommandé)
- **Disque**: 20 GB espace libre
- **Réseau**: Connexion Internet stable

---

## 🚀 Installation Rapide (10 minutes)

### Étape 1: Cloner le Projet

```bash
git clone https://github.com/your-repo/smartmaintain.git
cd smartmaintain
```

### Étape 2: Configuration Environnement

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer les variables (voir section Variables ci-dessous)
notepad .env  # Windows
```

### Étape 3: Lancer les Services

```bash
# Démarrer tous les services
docker-compose up -d

# Attendre initialisation (30-60 secondes)
timeout /t 60 /nobreak
```

### Étape 4: Vérifier l'Installation

```bash
# Vérifier que tous les conteneurs sont actifs
docker-compose ps

# Tester les services
curl http://localhost:5000/health
curl http://localhost:5001/health
curl http://localhost:5002/health
curl http://localhost:5003/health
curl http://localhost:5004/health
```

### Étape 5: Accéder à l'Application

```
Frontend: http://localhost:3000
API Gateway: http://localhost:5000
```

**Identifiants par défaut**:
- Email: `admin@smartmaintain.com`
- Password: `admin123` (à changer en production!)

---

## ⚙️ Variables d'Environnement

### Fichier `.env`

```bash
# ===== Base de Données PostgreSQL =====
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123           # ⚠️ Changer en production!
POSTGRES_DB=smartmaintain
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# ===== Redis =====
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=                         # Laisser vide pour dev

# ===== JWT Authentification =====
JWT_SECRET_KEY=your-secret-key-here     # ⚠️ Générer une clé unique!
JWT_ACCESS_TOKEN_EXPIRES=3600           # 1 heure

# ===== Mode ML =====
MOCK_ML=false                           # false = modèles réels, true = mode simulation

# ===== Email Service (Optionnel) =====
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@smartmaintain.com

# ===== URLs Services Internes =====
AUTH_SERVICE_URL=http://auth:5001
ML_SERVICE_URL=http://ml:5003
ALERTES_SERVICE_URL=http://alertes:5002
IOT_SERVICE_URL=http://iot:5004

# ===== CORS (Frontend) =====
FRONTEND_URL=http://localhost:3000

# ===== Logs =====
LOG_LEVEL=INFO                          # DEBUG, INFO, WARNING, ERROR
```

### Générer une Clé JWT Sécurisée

```bash
# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})

# Python
python -c "import secrets; print(secrets.token_hex(32))"

# OpenSSL (Git Bash)
openssl rand -hex 32
```

---

## 🐳 Architecture Docker

### Services Déployés

```yaml
smartmaintain/
├── postgres (PostgreSQL 15)           # Port 5432
├── redis (Redis 7)                    # Port 6379
├── gateway (Python Flask)             # Port 5000
├── auth (Python Flask)                # Port 5001
├── alertes (Python Flask)             # Port 5002
├── ml (Python Flask + XGBoost)        # Port 5003
├── iot (Python Flask)                 # Port 5004
└── frontend (React + Vite)            # Port 3000
```

### Volumes Persistants

```
smartmaintain_postgres_data    # Données PostgreSQL
smartmaintain_redis_data       # Données Redis
```

---

## 🔧 Initialisation Base de Données

### Schéma Automatique

Les tables sont créées automatiquement au démarrage via les migrations dans chaque service:
- `backend/auth/models/` → Tables users, plants, components
- `backend/alertes/models/` → Tables alerts
- `backend/ml/migrations/` → Tables prediction_log, prediction_feedback

### Vérifier les Tables

```bash
# Se connecter à PostgreSQL
docker-compose exec postgres psql -U postgres smartmaintain

# Lister les tables
\dt

# Sortir
\q
```

### Créer un Utilisateur Admin

```bash
docker-compose exec auth python -c "
from app import create_app
from models.models import User, db
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = User(
        email='admin@smartmaintain.com',
        password_hash=generate_password_hash('admin123'),
        role='admin',
        first_name='Admin',
        last_name='System'
    )
    db.session.add(admin)
    db.session.commit()
    print('✅ Admin créé!')
"
```

---

## 📦 Installation Modèles ML

Les modèles ML sont inclus dans `backend/ml/models/trained/`. Si vous voulez les entraîner avec vos propres données:

```bash
# Voir le guide ML
cat docs/ML_GUIDE.md
```

---

## ✅ Tests de Validation

### Test 1: Services Actifs

```bash
docker-compose ps
```

**Attendu**: Tous les services `Up`

### Test 2: API Health Checks

```bash
# Gateway
curl http://localhost:5000/health

# Auth
curl http://localhost:5001/health

# Alertes
curl http://localhost:5002/health

# ML
curl http://localhost:5003/health

# IoT
curl http://localhost:5004/health
```

**Attendu**: Tous retournent `{"status": "ok"}`

### Test 3: Connexion Frontend

1. Ouvrir http://localhost:3000
2. Voir page de connexion
3. Se connecter avec admin/admin123
4. Accéder au Dashboard

### Test 4: Flux de Données

```bash
# Vérifier que l'IoT publie des données
docker-compose logs -f iot | head -n 20

# Vérifier que ML reçoit et prédit
docker-compose logs -f ml | head -n 20

# Vérifier que les alertes sont créées
docker-compose logs -f alertes | head -n 20
```

---

## 🚨 Résolution Problèmes Courants

### Problème: Conteneur ne démarre pas

```bash
# Voir les logs d'erreur
docker-compose logs [service-name]

# Exemples:
docker-compose logs postgres
docker-compose logs ml
```

### Problème: "Port already in use"

```bash
# Trouver le processus utilisant le port
netstat -ano | findstr :5000

# Arrêter le processus (remplacer PID)
taskkill /PID [process-id] /F
```

### Problème: Base de données vide

```bash
# Réinitialiser la base
docker-compose down -v
docker-compose up -d
```

### Problème: Modèles ML non chargés

```bash
# Vérifier les fichiers
docker-compose exec ml ls -la /app/models/trained/

# Relancer le service
docker-compose restart ml
```

### Problème: Frontend ne se connecte pas

1. Vérifier CORS dans `.env`: `FRONTEND_URL=http://localhost:3000`
2. Vérifier Gateway actif: `curl http://localhost:5000/health`
3. Vider le cache navigateur (Ctrl+Shift+Del)

---

## 🔄 Commandes Utiles

### Gestion Services

```bash
# Démarrer tout
docker-compose up -d

# Arrêter tout
docker-compose down

# Redémarrer un service
docker-compose restart [service-name]

# Voir les logs
docker-compose logs -f [service-name]

# Reconstruire une image
docker-compose build [service-name]
docker-compose up -d [service-name]
```

### Maintenance

```bash
# Nettoyer les conteneurs arrêtés
docker system prune

# Voir l'utilisation disque
docker system df

# Sauvegarder la base de données
docker-compose exec -T postgres pg_dump -U postgres smartmaintain > backup.sql

# Restaurer la base
docker-compose exec -T postgres psql -U postgres smartmaintain < backup.sql
```

---

## 🔐 Sécurité Production

### Checklist Avant Déploiement

- [ ] Changer `POSTGRES_PASSWORD`
- [ ] Générer nouveau `JWT_SECRET_KEY`
- [ ] Configurer HTTPS/TLS
- [ ] Activer rate limiting
- [ ] Configurer firewall
- [ ] Mettre à jour les mots de passe admin
- [ ] Désactiver les comptes de test
- [ ] Configurer backup automatique
- [ ] Activer monitoring

Voir `docs/04_DEPLOYMENT.md` pour plus de détails.

---

## 📞 Support

- **Documentation complète**: `docs/`
- **Architecture**: `docs/ARCHITECTURE.md`
- **Développement**: `docs/02_DEVELOPMENT.md`
- **Dépannage**: consulter les contrôles de santé et les logs décrits dans ce guide.

---

**Installation terminée avec succès!** 🎉

Prochaine étape: Lire `docs/02_DEVELOPMENT.md` pour le développement.
