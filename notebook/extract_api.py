import requests

CLIENT_ID = "PAR_apipmpt_4783901a0ab206c1a6a738202ac282ec79de0604576e37418c87f98980488626"
CLIENT_SECRET = "669467172cf7235590f9a04c3dec140ed69d40aae2460a752282a565bddcc324"

# 1. Token
url_token = (
    "https://entreprise.francetravail.fr/"
    "connexion/oauth2/access_token?realm=%2Fpartenaire"
)

payload_token = {
    "grant_type": "client_credentials",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "scope": "api_rome-metiersv1"
}

res_token = requests.post(
    url_token,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data=payload_token
)

print("TOKEN STATUS:", res_token.status_code)
print("TOKEN BODY:", res_token.text)
res_token.raise_for_status()
access_token = res_token.json()["access_token"]
print(":white_check_mark: Authentification réussie")

# 2. Appels API
urls = [
    "https://api.francetravail.io/partenaire/rome-metiers/v1/metiers",
    "https://api.francetravail.io/partenaire/rome-metiers/v1/appellations",
    "https://api.francetravail.io/partenaire/rome-metiers/v1/fiches-rome",
]

headers_rome = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

for url in urls:
    print(f"\nTEST: {url}")
    response = requests.get(url, headers=headers_rome)
    print("STATUS:", response.status_code)
    print("BODY:", repr(response.text[:300]))