import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv('FT_CLIENT_ID')
CLIENT_SECRET = os.getenv('FT_CLIENT_SECRET')

# 1. Obtenir le token
def get_token():
    url = "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "api_offresdemploiv2 o2dsoffre"
    }
    response = requests.post(url, data=data)
    token = response.json().get("access_token")
    print(f"Token OK : {token[:20]}..." if token else "ERREUR token")
    return token

# 2. Récupérer les offres
def get_offres(token):
    url = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"motsCles": "data", "departement": "75", "range": "0-9"}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    print(f"Offres trouvées : {len(data.get('resultats', []))}")
    return data

if __name__ == "__main__":
    token = get_token()
    if token:
        offres = get_offres(token)
        with open("data/raw/offres_ft_test.json", "w") as f:
            json.dump(offres, f, ensure_ascii=False, indent=2)
        print("Fichier sauvegardé : data/raw/offres_ft_test.json")
