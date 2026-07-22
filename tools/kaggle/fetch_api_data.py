"""
Script pour récupérer des données JSON depuis une API
======================================================
Utilisez ce script pour télécharger des données depuis une API REST.
"""

import requests
import json
import sys
from pathlib import Path


def fetch_api_data(api_key: str, base_url: str = None, output_file: str = "api_data.json"):
    """
    Récupère des données JSON depuis une API.
    
    Args:
        api_key: Clé API ou identifiant de ressource
        base_url: URL de base de l'API (optionnel)
        output_file: Nom du fichier de sortie JSON
    """
    
    # Exemple 1: Si c'est une clé dans l'URL
    if base_url:
        url = f"{base_url}/{api_key}"
    else:
        # Exemple 2: Si c'est un paramètre de requête
        # Modifiez selon votre API
        url = f"https://api.example.com/data?key={api_key}"
    
    print(f"📡 Récupération depuis: {url}")
    
    try:
        # Requête GET avec timeout
        response = requests.get(url, timeout=30)
        
        # Vérifier le statut
        response.raise_for_status()
        
        # Parser JSON
        data = response.json()
        
        # Sauvegarder dans un fichier
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Données sauvegardées dans: {output_path}")
        print(f"📊 Taille: {len(json.dumps(data))} caractères")
        
        return data
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ Erreur HTTP: {e}")
        print(f"   Status code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        return None
        
    except requests.exceptions.Timeout:
        print("❌ Timeout: L'API ne répond pas")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur de connexion: {e}")
        return None
        
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON: {e}")
        print(f"   Response: {response.text[:200]}")
        return None


# ==============================================================================
# MÉTHODES COMMUNES D'ACCÈS AUX APIs
# ==============================================================================

def method_1_url_path(api_key: str):
    """Méthode 1: Clé dans le chemin de l'URL"""
    url = f"https://api.example.com/data/{api_key}"
    response = requests.get(url)
    return response.json()


def method_2_query_param(api_key: str):
    """Méthode 2: Clé comme paramètre de requête"""
    url = "https://api.example.com/data"
    params = {"key": api_key}
    response = requests.get(url, params=params)
    return response.json()


def method_3_header(api_key: str):
    """Méthode 3: Clé dans les headers (Authorization)"""
    url = "https://api.example.com/data"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.get(url, headers=headers)
    return response.json()


def method_4_api_key_header(api_key: str):
    """Méthode 4: Clé dans header X-API-Key"""
    url = "https://api.example.com/data"
    headers = {"X-API-Key": api_key}
    response = requests.get(url, headers=headers)
    return response.json()


# ==============================================================================
# USAGE PRINCIPAL
# ==============================================================================

if __name__ == "__main__":
    # Votre clé API
    API_KEY = "KGAT_e61ac6c7270890a765eb0eb37ca0a931"
    
    print("🔑 API Key:", API_KEY)
    print("\n" + "="*60)
    print("Choisissez la méthode d'accès à l'API:")
    print("="*60)
    print("1. Clé dans l'URL: https://api.example.com/data/{key}")
    print("2. Paramètre de requête: ?key={key}")
    print("3. Header Authorization: Bearer {key}")
    print("4. Header X-API-Key: {key}")
    print("5. Spécifier une URL complète")
    print("="*60)
    
    # **IMPORTANT**: Remplacez par l'URL réelle de votre API
    # Exemples courants:
    
    # Si c'est Kaggle:
    # url = f"https://www.kaggle.com/api/v1/datasets/download/{API_KEY}"
    
    # Si c'est une API publique:
    # url = f"https://api.domain.com/v1/data/{API_KEY}"
    
    # Si c'est une API locale:
    # url = f"http://localhost:8000/api/data/{API_KEY}"
    
    # Exemple d'utilisation:
    print("\n⚠️  ATTENTION: Vous devez spécifier l'URL de l'API!")
    print("   Modifiez ce script avec l'URL correcte.\n")
    
    # Décommentez et adaptez selon votre API:
    # data = fetch_api_data(API_KEY, base_url="https://api.example.com/data")


# ==============================================================================
# ALTERNATIVE: CURL COMMAND
# ==============================================================================

def generate_curl_commands(api_key: str):
    """Génère des commandes curl pour tester manuellement"""
    print("\n📋 Commandes curl pour tester:")
    print("="*60)
    
    print("\n1. Clé dans URL:")
    print(f'curl "https://api.example.com/data/{api_key}" > data.json')
    
    print("\n2. Paramètre de requête:")
    print(f'curl "https://api.example.com/data?key={api_key}" > data.json')
    
    print("\n3. Authorization header:")
    print(f'curl -H "Authorization: Bearer {api_key}" https://api.example.com/data > data.json')
    
    print("\n4. X-API-Key header:")
    print(f'curl -H "X-API-Key: {api_key}" https://api.example.com/data > data.json')
    
    print("\n" + "="*60)


if __name__ == "__main__":
    # Générer les commandes curl
    generate_curl_commands(API_KEY)
