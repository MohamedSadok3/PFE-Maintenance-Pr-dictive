# Kaggle Tools - SmartMaintain

Scripts et outils pour télécharger datasets depuis Kaggle.

---

## 🚀 Quick Start

### 1. Obtenir Token API Kaggle

1. Aller sur https://www.kaggle.com/settings
2. Section "API" → "Create New API Token"
3. Télécharger `kaggle.json`

### 2. Configuration Windows

```powershell
# Exécuter le script d'installation
.\setup_kaggle.ps1
```

**OU** manuellement:

```powershell
# Créer dossier .kaggle
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.kaggle"

# Copier kaggle.json
Copy-Item "Downloads\kaggle.json" "$env:USERPROFILE\.kaggle\kaggle.json"
```

### 3. Installer Kaggle CLI

```bash
pip install kaggle
```

### 4. Tester

```bash
kaggle datasets list -s "bearing"
```

---

## 📁 Scripts Disponibles

### `setup_kaggle.ps1`

Script PowerShell pour configuration automatique.

```powershell
.\setup_kaggle.ps1
```

**Actions**:
- Crée `~/.kaggle/`
- Configure `kaggle.json`
- Teste la connexion

### `download_kaggle_data.py`

Script Python complet pour télécharger datasets.

```bash
# Configuration
python download_kaggle_data.py --setup YOUR_USERNAME

# Télécharger un dataset
python download_kaggle_data.py --download uciml/iris

# Rechercher
python download_kaggle_data.py --search "bearing"
```

### `download_kaggle_dataset.py`

Script Python simple pour téléchargement rapide.

```python
from download_kaggle_dataset import download_dataset

download_dataset("brjapon/cwru-bearing-datasets", "./datasets/bearing")
```

### `extract_kaggle_tokens.py`

Utilitaire pour extraire et valider tokens API.

```bash
python extract_kaggle_tokens.py
```

### `fetch_api_data.py`

Script générique pour récupérer données depuis APIs.

```bash
python fetch_api_data.py --url "https://api.example.com" --key "YOUR_KEY"
```

---

## 📊 Datasets Recommandés

### Pour Moteur Électrique

**Dataset**: CWRU Bearing Data  
**Kaggle**: `brjapon/cwru-bearing-datasets`  
**Taille**: ~50 MB

```bash
kaggle datasets download -d brjapon/cwru-bearing-datasets --unzip
```

### Pour Pompe Hydraulique

**Dataset**: Pump Sensor Data  
**Kaggle**: `nphantawee/pump-sensor-data`  
**Taille**: ~20 MB

```bash
kaggle datasets download -d nphantawee/pump-sensor-data --unzip
```

### Pour Compresseur

**Dataset**: Compressor Data  
**Kaggle**: `pythonkumar/compressor-data`  
**Taille**: ~15 MB

```bash
kaggle datasets download -d pythonkumar/compressor-data --unzip
```

---

## 🔧 Configuration `kaggle.json`

### Format Fichier

```json
{
  "username": "your-username",
  "key": "your-api-key"
}
```

### Emplacement

**Windows**: `C:\Users\YOUR_NAME\.kaggle\kaggle.json`  
**Linux/Mac**: `~/.kaggle/kaggle.json`

### Permissions (Linux/Mac)

```bash
chmod 600 ~/.kaggle/kaggle.json
```

---

## 🐛 Troubleshooting

### Erreur: "401 Unauthorized"

✅ **Solution**:
- Vérifier username correct dans `kaggle.json`
- Vérifier API key valide
- Re-générer token sur Kaggle si nécessaire

### Erreur: "Could not find kaggle.json"

✅ **Solution**:
- Vérifier fichier dans `~/.kaggle/kaggle.json`
- Exécuter `setup_kaggle.ps1`

### Erreur: "403 Forbidden"

✅ **Solution**:
- Accepter les règles du dataset sur Kaggle.com
- Cliquer "Accept" sur la page du dataset

---

## 📝 Exemples d'Utilisation

### Téléchargement Basique

```bash
# Rechercher datasets
kaggle datasets list -s "predictive maintenance"

# Télécharger
kaggle datasets download -d OWNER/DATASET-NAME

# Décompresser
Expand-Archive dataset.zip -DestinationPath ./datasets/
```

### Téléchargement avec Python

```python
import kaggle

# Télécharger dataset
kaggle.api.dataset_download_files(
    'brjapon/cwru-bearing-datasets',
    path='./datasets/bearing',
    unzip=True
)
```

### Recherche Avancée

```bash
# Par mots-clés
kaggle datasets list -s "bearing fault detection" --max-size 100000000

# Par popularité
kaggle datasets list --sort-by votes

# Par date
kaggle datasets list --sort-by updated
```

---

## 🔗 Liens Utiles

- **Documentation Kaggle API**: https://www.kaggle.com/docs/api
- **Datasets Kaggle**: https://www.kaggle.com/datasets
- **Pip Package**: https://pypi.org/project/kaggle/

---

## 📞 Support

Pour aide avec Kaggle:
- Documentation principale: [../docs/ML_GUIDE.md](../../smartmaintain/docs/ML_GUIDE.md)
- Issues Kaggle API: https://github.com/Kaggle/kaggle-api/issues

---

**Configuration Actuelle**: ✅ Kaggle configuré (`mohamedsadoksouguir`)  
**Fichier**: `C:\Users\Mohamed Sadok\.kaggle\kaggle.json`
