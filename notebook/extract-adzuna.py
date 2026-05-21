import requests
import pandas as pd
import time

APP_ID = "0f5ddca8"
APP_KEY = "302e8693543aa36b934fc74de49faed7"

all_jobs = []
page = 1

print("Recuperation des offres Ile-de-France en cours...")

while True:
    url = f"https://api.adzuna.com/v1/api/jobs/fr/search/{page}"
    
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": 50,
        "where": "Ile-de-France",
        "distance": 30,
        "content-type": "application/json"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
    except Exception as e:
        print(f"Erreur reseau page {page}: {e}")
        time.sleep(5)
        continue

    if response.status_code != 200:
        print(f"Erreur page {page}: {response.status_code}")
        print("BODY:", response.text)
        break
    
    data = response.json()
    results = data.get("results", [])
    total = data.get("count", 0)
    
    if not results:
        print("Plus de resultats")
        break
    
    for job in results:
        all_jobs.append({
            "titre": job.get("title", ""),
            "entreprise": job.get("company", {}).get("display_name", ""),
            "lieu": job.get("location", {}).get("display_name", ""),
            "salaire_min": job.get("salary_min", ""),
            "salaire_max": job.get("salary_max", ""),
            "date": job.get("created", ""),
            "contrat": job.get("contract_time", ""),
            "categorie": job.get("category", {}).get("label", ""),
            "description": job.get("description", ""),
            "url": job.get("redirect_url", "")
        })
    
    print(f"Page {page} - {len(all_jobs)}/{total} offres recuperees")
    
    # Sauvegarde a chaque page
    df_temp = pd.DataFrame(all_jobs)
    df_temp.to_csv("offres_idf.csv", index=False, encoding="utf-8-sig")
    
    if page >= 250:
        print("Limite 250 pages atteinte")
        break
    
    page += 1
    time.sleep(0.5)

# Sauvegarde finale
df = pd.DataFrame(all_jobs)
df.to_csv("offres_idf.csv", index=False, encoding="utf-8-sig")
print(f"TERMINE - {len(df)} offres sauvegardees dans offres_idf.csv")