import requests
import pandas as pd
from datetime import datetime
import time

CLIENT_ID = "PAR_apipmpt_4783901a0ab206c1a6a738202ac282ec79de0604576e37418c87f98980488626"
CLIENT_SECRET = "669467172cf7235590f9a04c3dec140ed69d40aae2460a752282a565bddcc324"

# ============================================================
# ETAPE 1 : TOKEN
# ============================================================

res_token = requests.post(
    "https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "api_offresdemploiv2 o2dsoffre api_rome-metiersv1 nomenclatureRome"
    }
)

print("TOKEN STATUS:", res_token.status_code)

if res_token.status_code != 200:
    print("ERREUR TOKEN:", res_token.json())
    exit()

access_token = res_token.json()["access_token"]
print("Token OK !")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/json"
}

# ============================================================
# ETAPE 2 : COLLECTE OFFRES IDF
# ============================================================

departements = ["75", "77", "78", "91", "92", "93", "94", "95"]
all_offres = []

for dept in departements:
    start = 0
    print(f"\nDepartement {dept}...")

    while True:
        r = requests.get(
            "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search",
            headers=headers,
            params={
                "departement": dept,
                "range": f"{start}-{start + 149}",
                "sort": 1
            }
        )

        if r.status_code in [200, 206]:
            data = r.json()
            offres = data.get("resultats", [])

            for o in offres:
                all_offres.append({
                    "titre": o.get("intitule", ""),
                    "code_rome": o.get("romeCode", ""),
                    "appellation_rome": o.get("appellationlibelle", ""),
                    "entreprise": o.get("entreprise", {}).get("nom", ""),
                    "lieu": o.get("lieuTravail", {}).get("libelle", ""),
                    "code_postal": o.get("lieuTravail", {}).get("codePostal", ""),
                    "departement": dept,
                    "contrat": o.get("typeContratLibelle", ""),
                    "experience": o.get("experienceLibelle", ""),
                    "salaire": o.get("salaire", {}).get("libelle", ""),
                    "description": o.get("description", "")[:300],
                    "url": o.get("origineOffre", {}).get("urlOrigine", ""),
                    "date_publication": o.get("dateCreation", ""),
                    "date_import": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

            print(f"  {len(offres)} offres (total: {len(all_offres)})")

            if len(offres) < 150:
                break

            start += 150
            time.sleep(0.3)

        elif r.status_code == 204:
            print(f"  Dept {dept} - Aucune offre")
            break
        else:
            print(f"  Erreur {r.status_code}: {r.text[:200]}")
            break

# ============================================================
# ETAPE 3 : SAUVEGARDE
# ============================================================

df = pd.DataFrame(all_offres)

# Sauvegarde CSV
df.to_csv("data/offres_ft_idf.csv", index=False, encoding="utf-8-sig")
print(f"\nCSV sauvegarde : data/offres_ft_idf.csv")

# Injection SQLite
import sqlite3
conn = sqlite3.connect("data/database.db")
df.to_sql("offres_ft", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

print(f"\nTERMINE - {len(df)} offres FT sauvegardees")
print(f"Codes ROME uniques : {df['code_rome'].nunique()}")
print(f"Departements : {df['departement'].value_counts().to_dict()}")