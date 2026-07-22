"""
Extraire des tokens/données JSON depuis Kaggle
===============================================
Récupère les données d'un dataset Kaggle et les exporte en JSON.
"""

import json
import pandas as pd
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi


def download_and_extract_json(dataset_name, output_json="kaggle_data.json"):
    """
    Télécharge un dataset Kaggle et l'exporte en JSON.
    
    Args:
        dataset_name: Format "owner/dataset-name"
        output_json: Nom du fichier JSON de sortie
    """
    print(f"\n📥 Téléchargement: {dataset_name}")
    
    # Initialiser l'API Kaggle
    api = KaggleApi()
    api.authenticate()
    
    # Créer un dossier temporaire
    temp_dir = Path("./temp_kaggle")
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Télécharger le dataset
        print("⏳ Téléchargement en cours...")
        api.dataset_download_files(
            dataset_name,
            path=str(temp_dir),
            unzip=True
        )
        
        print("✅ Téléchargement terminé!")
        
        # Lister les fichiers téléchargés
        files = list(temp_dir.glob("*"))
        print(f"\n📁 {len(files)} fichier(s) trouvé(s):")
        for file in files:
            print(f"  - {file.name}")
        
        # Chercher les fichiers CSV/JSON
        data_files = []
        for ext in ['.csv', '.json', '.txt']:
            data_files.extend(temp_dir.glob(f"*{ext}"))
        
        if not data_files:
            print("\n⚠️  Aucun fichier CSV/JSON trouvé")
            return None
        
        # Traiter le premier fichier trouvé
        data_file = data_files[0]
        print(f"\n🔄 Conversion: {data_file.name} → JSON")
        
        # Lire selon le type de fichier
        if data_file.suffix == '.csv':
            # Lire CSV
            df = pd.read_csv(data_file)
            print(f"   Lignes: {len(df)}, Colonnes: {len(df.columns)}")
            
            # Convertir en JSON
            data = df.to_dict(orient='records')
            
        elif data_file.suffix == '.json':
            # Déjà JSON
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        else:
            print(f"   Type de fichier non supporté: {data_file.suffix}")
            return None
        
        # Sauvegarder en JSON
        output_path = Path(output_json)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ JSON créé: {output_path}")
        print(f"   Taille: {output_path.stat().st_size / 1024:.2f} KB")
        
        if isinstance(data, list):
            print(f"   Éléments: {len(data)}")
        
        return data
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return None
    
    finally:
        # Nettoyer les fichiers temporaires (optionnel)
        # import shutil
        # shutil.rmtree(temp_dir)
        pass


def extract_tokens_from_csv(csv_file, token_column="token", output_json="tokens.json"):
    """
    Extrait une colonne spécifique (tokens) d'un CSV vers JSON.
    
    Args:
        csv_file: Chemin du fichier CSV
        token_column: Nom de la colonne contenant les tokens
        output_json: Fichier JSON de sortie
    """
    print(f"\n🔍 Extraction des tokens depuis: {csv_file}")
    
    try:
        # Lire le CSV
        df = pd.read_csv(csv_file)
        print(f"   Colonnes disponibles: {list(df.columns)}")
        
        if token_column not in df.columns:
            print(f"\n⚠️  Colonne '{token_column}' non trouvée!")
            print(f"   Colonnes disponibles: {list(df.columns)}")
            
            # Afficher les premières lignes
            print("\n📊 Aperçu des données:")
            print(df.head())
            return None
        
        # Extraire les tokens
        tokens = df[token_column].tolist()
        
        # Sauvegarder en JSON
        output = {
            "tokens": tokens,
            "count": len(tokens),
            "source": csv_file
        }
        
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Tokens extraits: {len(tokens)}")
        print(f"   Sauvegardés dans: {output_json}")
        
        return tokens
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return None


def dataset_to_json_tokens(dataset_name, output_json="dataset_tokens.json"):
    """
    Télécharge un dataset et extrait tous les tokens/données en JSON.
    
    Args:
        dataset_name: Format "owner/dataset-name"
        output_json: Fichier JSON de sortie
    """
    print("="*70)
    print("  📊 EXTRACTION TOKENS DEPUIS KAGGLE")
    print("="*70)
    
    # Télécharger et extraire
    data = download_and_extract_json(dataset_name, output_json)
    
    if data:
        print("\n" + "="*70)
        print("  ✅ SUCCÈS!")
        print("="*70)
        print(f"\n📄 Fichier JSON créé: {output_json}")
        
        # Afficher un aperçu
        if isinstance(data, list) and len(data) > 0:
            print(f"\n📋 Aperçu (premier élément):")
            print(json.dumps(data[0], indent=2, ensure_ascii=False)[:500])
            if len(json.dumps(data[0], indent=2)) > 500:
                print("...")
    
    return data


# =============================================================================
# EXEMPLES D'UTILISATION
# =============================================================================

if __name__ == "__main__":
    print("="*70)
    print("  🎯 EXTRACTION DE TOKENS DEPUIS KAGGLE")
    print("="*70)
    
    print("\n💡 Méthodes disponibles:\n")
    
    print("1️⃣  Télécharger un dataset complet en JSON:")
    print("    dataset_to_json_tokens('owner/dataset-name')\n")
    
    print("2️⃣  Extraire des tokens d'un CSV local:")
    print("    extract_tokens_from_csv('data.csv', token_column='token')\n")
    
    print("3️⃣  Télécharger et extraire:")
    print("    download_and_extract_json('owner/dataset-name')\n")
    
    print("="*70)
    print("\n📝 Exemples concrets:")
    print("="*70)
    
    # Exemple 1: Dataset simple
    print("\n# Exemple 1: Iris dataset → JSON")
    print("dataset_to_json_tokens('uciml/iris', 'iris.json')")
    
    # Exemple 2: Bearing dataset
    print("\n# Exemple 2: Bearing dataset → JSON")
    print("dataset_to_json_tokens('brjapon/cwru-bearing-datasets', 'bearing.json')")
    
    # Exemple 3: Extraire depuis CSV local
    print("\n# Exemple 3: Extraire tokens d'un CSV")
    print("extract_tokens_from_csv('data.csv', token_column='text', output_json='tokens.json')")
    
    print("\n" + "="*70)
    print("💡 DÉCOMMENTEZ UNE LIGNE CI-DESSOUS POUR TESTER:")
    print("="*70 + "\n")
    
    # Décommentez pour tester:
    
    # Test 1: Dataset Iris (petit et rapide)
    # dataset_to_json_tokens('uciml/iris', 'iris_data.json')
    
    # Test 2: Si vous avez un CSV local
    # extract_tokens_from_csv('mon_fichier.csv', token_column='colonne_tokens')
    
    # Test 3: Dataset spécifique
    # Remplacez par votre dataset Kaggle
    # dataset_to_json_tokens('OWNER/DATASET-NAME', 'output.json')
    
    print("✅ Script prêt! Décommentez une ligne pour l'exécuter.\n")
