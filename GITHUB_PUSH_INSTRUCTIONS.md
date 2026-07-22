# Instructions pour Pousser vers GitHub

**Date**: 22 Juillet 2026  
**Projet**: SmartMaintain v2.0

---

## ✅ Étape 1: Créer le Repository sur GitHub (FAIT EN LOCAL)

Le commit initial est créé localement:
```
✅ Commit: 4f23039
✅ Fichiers: 178 fichiers
✅ Lignes: 28,231 insertions
✅ Message: "feat: Initial commit - SmartMaintain v2.0 (refactored)"
```

---

## 🌐 Étape 2: Créer Repository sur GitHub.com

### Option A: Via Interface Web (Recommandé si pas de 'gh')

1. **Ouvrir navigateur** → https://github.com/new

2. **Remplir formulaire**:
   - **Repository name**: `smartmaintain`
   - **Description**: `Plateforme de maintenance prédictive avec Machine Learning - Surveillance temps réel de machines industrielles`
   - **Visibilité**: ☑️ Public (ou Private selon préférence)
   - **⚠️ IMPORTANT**: NE PAS cocher:
     - ❌ Add a README file
     - ❌ Add .gitignore
     - ❌ Choose a license

3. **Cliquer** "Create repository"

4. **GitHub affichera la page "Quick setup"**

5. **Copier l'URL du repository** (format: `https://github.com/YOUR_USERNAME/smartmaintain.git`)

---

## 🚀 Étape 3: Pousser vers GitHub

### Une fois le repository créé sur GitHub:

```powershell
# Naviguer vers le projet (si pas déjà là)
cd "c:\Users\Mohamed Sadok\Desktop\PFE Maintenance prédictive"

# Ajouter remote (remplacer YOUR_USERNAME par votre nom GitHub)
git remote add origin https://github.com/YOUR_USERNAME/smartmaintain.git

# Vérifier remote
git remote -v

# Renommer branche en 'main' (convention moderne)
git branch -M main

# Pousser vers GitHub
git push -u origin main
```

**⚠️ Si erreur d'authentification**:
- GitHub ne supporte plus les mots de passe HTTPS
- Utiliser **Personal Access Token** ou **SSH**

---

## 🔐 Étape 4: Authentification GitHub

### Option A: Personal Access Token (HTTPS)

1. Aller sur https://github.com/settings/tokens
2. Cliquer "Generate new token (classic)"
3. **Note**: `SmartMaintain Token`
4. **Expiration**: 90 days (ou No expiration)
5. **Scopes**: Cocher `repo` (tous les sous-items)
6. Générer token
7. **COPIER LE TOKEN** (vous ne le reverrez plus!)

Lors du `git push`, entrer:
```
Username: YOUR_GITHUB_USERNAME
Password: VOTRE_TOKEN (pas votre mot de passe!)
```

### Option B: SSH (Recommandé pour usage long terme)

```powershell
# Générer clé SSH
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copier clé publique
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard

# Ajouter sur GitHub
# 1. Aller sur https://github.com/settings/keys
# 2. "New SSH key"
# 3. Coller la clé
# 4. Sauvegarder

# Changer remote en SSH
git remote set-url origin git@github.com:YOUR_USERNAME/smartmaintain.git

# Pousser
git push -u origin main
```

---

## 📋 Commandes Complètes (Copy-Paste)

### Après création repository sur GitHub:

```powershell
# Remplacer YOUR_USERNAME par votre nom GitHub
$username = "YOUR_USERNAME"

# Naviguer vers projet
cd "c:\Users\Mohamed Sadok\Desktop\PFE Maintenance prédictive"

# Ajouter remote
git remote add origin "https://github.com/$username/smartmaintain.git"

# Renommer branche
git branch -M main

# Pousser
git push -u origin main

# Vérifier
Write-Host "`n✅ Projet poussé vers GitHub!" -ForegroundColor Green
Write-Host "🌐 URL: https://github.com/$username/smartmaintain" -ForegroundColor Cyan
```

---

## ✅ Vérification Post-Push

Après `git push`, vérifier sur GitHub:

1. **Code**: 178 fichiers visibles
2. **README.md**: S'affiche sur page principale
3. **Commits**: 1 commit initial visible
4. **Structure**:
   ```
   smartmaintain/
   ├── backend/
   ├── frontend/
   ├── docs/
   └── docker-compose.yml
   ```

---

## 🎯 Étapes Suivantes (Optionnel)

### 1. Ajouter LICENSE

```powershell
# Créer LICENSE MIT
@"
MIT License

Copyright (c) 2026 Mohamed Sadok

Permission is hereby granted, free of charge, to any person obtaining a copy...
"@ | Out-File -FilePath "LICENSE" -Encoding utf8

git add LICENSE
git commit -m "docs: Add MIT license"
git push
```

### 2. Ajouter Topics/Tags sur GitHub

Sur la page du repo:
- Cliquer "⚙️" à côté de "About"
- Ajouter topics: `machine-learning`, `predictive-maintenance`, `xgboost`, `react`, `docker`, `microservices`, `iot`

### 3. Protéger Branche Main

Settings → Branches → Add rule:
- Branch name pattern: `main`
- ☑️ Require pull request before merging
- ☑️ Require status checks to pass

### 4. Setup GitHub Actions (CI/CD)

Créer `.github/workflows/ci.yml` pour tests automatiques.

---

## 🚨 Troubleshooting

### Erreur: "remote origin already exists"

```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/smartmaintain.git
```

### Erreur: "Authentication failed"

Utiliser Personal Access Token (voir Étape 4).

### Erreur: "Permission denied (publickey)"

Configurer SSH (voir Option B ci-dessus).

### Push trop lent (fichiers volumineux)

Les datasets `.npz` et `.npy` sont ignorés par `.gitignore`.
Si le push est lent, vérifier qu'ils ne sont pas inclus:

```powershell
git ls-files | Select-String ".npz|.npy"
# Devrait retourner vide
```

---

## 📞 Support

- **Documentation Git**: https://git-scm.com/doc
- **GitHub Docs**: https://docs.github.com/
- **Personal Access Tokens**: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token

---

**Prêt à pousser!** 🚀

Une fois le repository créé sur GitHub, exécuter:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/smartmaintain.git
git branch -M main
git push -u origin main
```
