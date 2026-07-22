# Guide Rapide - Push vers GitHub

## 🚀 3 Étapes Simples

### Étape 1: Créer Repository sur GitHub (2 minutes)

1. Aller sur **https://github.com/new**
2. Remplir:
   - **Nom**: `smartmaintain`
   - **Description**: `Plateforme maintenance prédictive ML - Surveillance temps réel machines industrielles`
   - **Visibilité**: Public
3. **⚠️ IMPORTANT**: NE PAS cocher "Initialize this repository with..."
4. Cliquer **"Create repository"**

### Étape 2: Copier URL Repository

GitHub affichera quelque chose comme:
```
https://github.com/YOUR_USERNAME/smartmaintain.git
```
**Copier cette URL!**

### Étape 3: Exécuter Script

```powershell
# Dans PowerShell:
cd "c:\Users\Mohamed Sadok\Desktop\PFE Maintenance prédictive"
.\push_to_github.ps1
```

Le script vous demandera:
- ✏️ Votre username GitHub
- ✅ Confirmation avant push

**C'est tout!** 🎉

---

## 🔐 Authentification

Si erreur "Authentication failed":

### Option A: Personal Access Token (Simple)

1. Aller sur https://github.com/settings/tokens
2. "Generate new token (classic)"
3. Cocher: `repo` (tous les sous-items)
4. Générer et **COPIER** le token
5. Lors du push, entrer:
   - Username: `votre_username`
   - Password: `le_token_copié` (PAS votre mot de passe!)

### Option B: SSH (Plus rapide après setup)

```powershell
# Générer clé
ssh-keygen -t ed25519 -C "votre_email@example.com"

# Copier clé publique
Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub" | Set-Clipboard

# Ajouter sur GitHub
# 1. https://github.com/settings/keys
# 2. "New SSH key"
# 3. Coller et sauvegarder

# Utiliser SSH URL au lieu de HTTPS
git remote set-url origin git@github.com:YOUR_USERNAME/smartmaintain.git
git push -u origin main
```

---

## ✅ Vérification

Après push, sur GitHub vous devriez voir:
- ✅ 178 fichiers
- ✅ README.md affiché
- ✅ Structure: smartmaintain/, tools/, docs/

---

## 🚨 Problèmes Courants

**"remote origin already exists"**
```powershell
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/smartmaintain.git
```

**"Permission denied"**
→ Utiliser Personal Access Token (voir ci-dessus)

**"Repository not found"**
→ Vérifier que le repository existe sur GitHub

---

## 📞 Aide

- 📖 Documentation complète: `GITHUB_PUSH_INSTRUCTIONS.md`
- 🔧 Script automatique: `push_to_github.ps1`

---

**Temps total**: ~5 minutes ⏱️  
**Difficulté**: Facile 🟢
