"""
Script pour télécharger des données depuis Kaggle
==================================================
Utilise votre token Kaggle pour télécharger des datasets.
"""

import json
import os
import sys
import argparse
from pathlib import Path
import subprocess


def create_kaggle_config(username: str, api_key: str):
    """
    Crée le fichier kaggle.json avec vos credentials.
    
    Args:
        username: Votre username Kaggle
        api_key: Votre clé API Kaggle (token)
    """
    # Chemin du dossier .kaggle
    kaggle_dir = Path.home() / ".kaggle"
    kaggle_file = kaggle_dir / "kaggle.json"
    
    # Créer le dossier s'il n'existe pas
    kaggle_dir.mkdir(exist_ok=True)
    
    # Créer le fichier de configuration
    config = {
        "username": username,
        "key": api_key
    }
    
    with open(kaggle_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Définir les permissions (important pour la sécurité)
    if os.name != 'nt':  # Unix/Linux/Mac
        os.chmod(kaggle_file, 0o600)
    
    print(f"✅ Fichier kaggle.json créé dans: {kaggle_file}")
    return kaggle_file


def check_kaggle_installation():
    """Vérifie si kaggle CLI est installé."""
    try:
        result = subprocess.run(['kaggle', '--version'], 
                              capture_output=True, 
                              text=True,
                              check=True)
        print(f"✅ Kaggle CLI installé: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Kaggle CLI n'est pas installé")
        print("   Installez-le avec: pip install kaggle")
        return False


def download_dataset(dataset_name: str, output_path: str = ".", unzip: bool = True):
    """
    Télécharge un dataset depuis Kaggle.
    
    Args:
        dataset_name: Nom du dataset (format: owner/dataset-name)
        output_path: Dossier de destination
        unzip: Décompresser automatiquement
    """
    print(f"\n📥 Téléchargement de: {dataset_name}")
    print(f"📁 Destination: {output_path}")
    
    # Créer le dossier de destination
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    # Construire la commande
    cmd = ['kaggle', 'datasets', 'download', '-d', dataset_name, '-p', output_path]
    
    if unzip:
        cmd.append('--unzip')
    
    try:
        # Exécuter la commande
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"✅ Dataset téléchargé avec succès!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du téléchargement:")
        print(e.stderr)
        return False


def search_datasets(query: str, limit: int = 10):
    """
    Recherche des datasets sur Kaggle.
    
    Args:
        query: Terme de recherche
        limit: Nombre de résultats (max 20)
    """
    print(f"\n🔍 Recherche: '{query}'")
    
    cmd = ['kaggle', 'datasets', 'list', '-s', query, '--max-size', str(limit)]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la recherche:")
        print(e.stderr)
        return False


def download_competition(competition_name: str, output_path: str = "."):
    """
    Télécharge les fichiers d'une compétition Kaggle.
    
    Args:
        competition_name: Nom de la compétition
        output_path: Dossier de destination
    """
    print(f"\n🏆 Téléchargement de la compétition: {competition_name}")
    
    Path(output_path).mkdir(parents=True, exist_ok=True)
    
    cmd = ['kaggle', 'competitions', 'download', '-c', competition_name, '-p', output_path]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"✅ Compétition téléchargée avec succès!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du téléchargement:")
        print(e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Télécharger des données depuis Kaggle',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  # 1. Configurer vos credentials
  python download_kaggle_data.py --setup YOUR_USERNAME

  # 2. Télécharger un dataset
  python download_kaggle_data.py --download uciml/iris

  # 3. Rechercher des datasets
  python download_kaggle_data.py --search "bearing fault"

  # 4. Télécharger une compétition
  python download_kaggle_data.py --competition titanic
        """
    )
    
    parser.add_argument('--setup', 
                       metavar='USERNAME',
                       help='Configurer kaggle.json avec votre username')
    
    parser.add_argument('--download', '-d',
                       metavar='DATASET',
                       help='Télécharger un dataset (format: owner/dataset-name)')
    
    parser.add_argument('--search', '-s',
                       metavar='QUERY',
                       help='Rechercher des datasets')
    
    parser.add_argument('--competition', '-c',
                       metavar='NAME',
                       help='Télécharger une compétition')
    
    parser.add_argument('--output', '-o',
                       default='./kaggle_data',
                       help='Dossier de destination (défaut: ./kaggle_data)')
    
    parser.add_argument('--no-unzip',
                       action='store_true',
                       help='Ne pas décompresser automatiquement')
    
    args = parser.parse_args()
    
    # Configuration
    if args.setup:
        API_KEY = "KGAT_e61ac6c7270890a765eb0eb37ca0a931"  # Votre token
        create_kaggle_config(args.setup, API_KEY)
        print("\n✅ Configuration terminée!")
        print("   Vous pouvez maintenant télécharger des datasets.")
        return
    
    # Vérifier l'installation de kaggle CLI
    if not check_kaggle_installation():
        print("\n📦 Installation de kaggle CLI...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'kaggle'], check=True)
            print("✅ Kaggle CLI installé!")
        except subprocess.CalledProcessError:
            print("❌ Impossible d'installer kaggle CLI")
            return
    
    # Télécharger un dataset
    if args.download:
        download_dataset(args.download, args.output, not args.no_unzip)
        return
    
    # Rechercher des datasets
    if args.search:
        search_datasets(args.search)
        return
    
    # Télécharger une compétition
    if args.competition:
        download_competition(args.competition, args.output)
        return
    
    # Si aucun argument, afficher l'aide
    parser.print_help()


if __name__ == "__main__":
    print("="*70)
    print("  📊 KAGGLE DATA DOWNLOADER")
    print("="*70)
    print()
    
    main()
