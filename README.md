# PPMT 

## :world_map:Issue Tree (Arbre des Problèmes)
```text
                                                ┌─► [JACK] Combien d'offres y a-t-il ? (API France Travail)
                       ┌─► 1. LA TENSION ───────┤
                       │                        └─► [BERNARD] Combien de candidats ? (Scraping Indeed)
                       │
PROBLÈME CENTRAL ──────┼─► 2. LE CABINET ───────┬─► [BERNARD] Quels sont les salaires réels ? (Scraping Glassdoor)
Comment rapprocher     │                        └─► [CLAIRE] Quel est le risque d'échec ? (Modèle ML)
recruteurs/candidats ? │
                       └─► 3. LE CANDIDAT ──────┬─► [CLAIRE] Quels métiers ont les mêmes compétences ?
                                                └─► [JACK] Quels Hard Skills manquent au CV ? (Streamlit)

#Structure du projet

PPMT/
├── data/                    # :warning: Données locales (Ignorées par Git)
│   ├── raw/                 # Fichiers bruts (JSON, HTML)
│   └── processed/           # Fichiers nettoyés (CSV)
├── notebook/                # Brouillons et Exploration
│   ├── jack_extract_api.ipynb
│   ├── bernard_scraping.ipynb  <-- Exploration d'Indeed ici !
│   └── claire_eda_ml.ipynb
├── sources/                 # Scripts automatisés (ETL)
│   ├── extract_api.py
│   ├── extract_scrape.py
│   └── transform_sql.py
├── webapp/                  # Interface utilisateur Streamlit
│   ├── app.py
│   └── models/              # Modèle ML sauvegardé (.pkl)
├── README.md                # Documentation du projet
├── requirements.txt         # Dépendances Python
└── schema_db.sql            # Structure vide de la base SQL

#Data Dictionnaire
#Data Dictionnaire (Suivi Qualité)

Source 1 (API France Travail) : ID Offre, Code ROME, Région. Risque : Salaires souvent manquants.
Source 2 (Scraping Indeed) : Volume d'offres concurrentes. Risque : Nettoyage de chaînes de caractères requis.
Source 3 (Scraping Glassdoor) : Salaires Minimum / Maximum. Risque : Données très textuelles à convertir en entiers.