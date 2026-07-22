"""
Téléchargement direct de datasets Kaggle sans CLI
===================================================
Alternative si kaggle CLI ne fonctionne pas.
"""

import json
import os
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi


def setup_kaggle_credentials():
    """Configure les credentials Kaggle."""
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_file = kaggle_dir / "kaggle.json"
    
    # Créer le dossier
    kaggle_dir.mkdir(exist_ok=True)
    
    # Credentials
    credentials = {
        "username": "mohamedsadoksouguir",
        "key": "KGAT_e61ac6c7270890a765eb0eb37ca0a931"
    }
    
    # Écrire le fichier
    with open(kaggle_file, 'w', encoding='utf-8') as f:
        json.dump(credentials, f, indent=2)
    
    # Permissions (Unix/Linux/Mac)
    if os.name != 'nt':
        os.chmod(kaggle_file, 0o600)
    
    print(f"✅ Credentials configurés: {kaggle_file}")
    return kaggle_file


def download_dataset(dataset_name, output_path="./kaggle_data"):
    """
    Télécharge un dataset Kaggle.
    
    Args:
        dataset_name: Format "owner/dataset-name"
        output_path: Dossier de destination
    """
    print(f"\n📥 Téléchargement: {dataset_name}")
    print(f"📁 Destination: {output_path}\n")
    
    # Initialiser l'API
    api = KaggleApi()
    api.authenticate()
    
    # Créer le dossier de destination
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    try:
        # Télécharger et décompresser
        api.dataset_download_files(
            dataset_name,
            path=output_path,
            unzip=True
        )
        
        print(f"\n✅ Dataset téléchargé avec succès!")
        print(f"📂 Fichiers dans: {output_path}")
        
        # Lister les fichiers téléchargés
        files = list(Path(output_path).glob("*"))
        print(f"\n📋 {len(files)} fichier(s) téléchargé(s):")
        for file in files[:10]:  # Afficher max 10 fichiers
            size = file.stat().st_size / (1024 * 1024)  # MB
            print(f"  - {file.name} ({size:.2f} MB)")
        
        if len(files) > 10:
            print(f"  ... et {len(files) - 10} autres fichiers")
            
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du téléchargement:")
        print(f"   {e}")
        return False


def list_datasets(search_term, max_results=10):
    """Liste les datasets correspondant à la recherche."""
    print(f"\n🔍 Recherche: '{search_term}'\n")
    
    api = KaggleApi()
    api.authenticate()
    
    try:
        datasets = api.dataset_list(search=search_term, page=1, max_size=max_results)
        
        if not datasets:
            print("Aucun dataset trouvé")
            return
        
        print(f"📊 {len(datasets)} dataset(s) trouvé(s):\n")
        
        for i, dataset in enumerate(datasets, 1):
            print(f"{i}. {dataset.ref}")
            print(f"   Titre: {dataset.title}")
            print(f"   Taille: {dataset.size / (1024*1024):.2f} MB")
            print(f"   Fichiers: {dataset.fileCount}")
            print()
            
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    print("="*70)
    print("  📊 KAGGLE DATASET DOWNLOADER (Python API)")
    print("="*70)
    
    # Configuration
    print("\n[1/3] Configuration des credentials...")
    setup_kaggle_credentials()
    
    print("\n[2/3] Exemples de datasets disponibles:")
    print("="*70)
    
    # Exemples
    examples = [
        ("uciml/iris", "Dataset Iris (classification)"),
        ("brjapon/cwru-bearing-datasets", "Bearing fault detection (maintenance prédictive)"),
        ("NASA/landslide-events", "Landslide events NASA"),
    ]
    
    for dataset, description in examples:
        print(f"\n  • {dataset}")
        print(f"    {description}")
        print(f"    Commande: download_dataset('{dataset}')")
    
    print("\n" + "="*70)
    print("\n[3/3] Pour télécharger un dataset, décommentez ci-dessous:")
    print("="*70)
    
    # Exemples d'utilisation (décommentez pour utiliser)
    
    # Exemple 1: Télécharger Iris dataset
    # download_dataset("uciml/iris", output_path="./data/iris")
    
    # Exemple 2: Télécharger bearing dataset
    # download_dataset("brjapon/cwru-bearing-datasets", output_path="./data/bearing")
    
    # Exemple 3: Rechercher des datasets
    # list_datasets("predictive maintenance")
    
    print("\n💡 Modifiez ce script et décommentez les lignes pour télécharger!")
    print("\nOu utilisez les fonctions directement:")
    print("  >>> from download_kaggle_dataset import download_dataset")
    print("  >>> download_dataset('uciml/iris')")
