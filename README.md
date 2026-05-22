# PPMT - Plateforme Predictive des Metiers en Tension

> Projet Data Engineering & Data Science - Soutenance 29/05/2026
> Equipe : Bernard | Claire

---

## Objectif

Identifier les metiers en tension sur le marche du travail francais en croisant
les donnees Adzuna et France Travail, et proposer une analyse predictive via
un dashboard interactif.

---

## Structure du projet

PPMT/
├── data/
│   ├── raw/
│   │   └── tous_les_codes_rome.json     # Referentiel codes ROME 4.0
│   ├── processed/                        # (vide - reserve aux futures exports)
│   ├── offres_idf.csv                   # Donnees brutes Adzuna
│   ├── offres_ft_idf.csv               # Donnees brutes France Travail
│   ├── offres_idf_clean.csv            # Adzuna nettoye (4 980 offres)
│   ├── offres_ft_idf_clean.csv         # France Travail nettoye (24 051 offres)
│   ├── itm_consolide.csv               # Metiers en tension consolides
│   ├── predictions_itm.csv             # Predictions ML
│   └── database.db                      # Base SQLite (~40 Mo)
├── sources/
│   ├── clean_adzuna.py                  # Nettoyage donnees Adzuna
│   ├── clean_ft.py                      # Nettoyage donnees France Travail
│   ├── create_db.py                     # Creation base SQLite
│   ├── mapping_adzuna_rome.py           # Mapping codes ROME + tension
│   └── extract_api_ft.py               # Extraction API France Travail
├── notebook/
│   ├── claire_analyse_tension.py        # Analyse ML tensions
│   ├── Extract_api.py                   # Extraction API
│   ├── Extract_scraping.py              # Scripts scraping
│   └── extract-adzuna.py               # Extraction Adzuna
├── webapp/
│   ├── app.py                           # Dashboard Streamlit
│   └── models/
│       ├── modele_itm.pkl              # Modele ML Random Forest
│       ├── scaler_itm.pkl              # Scaler normalisation
│       └── features_itm.pkl            # Features du modele
└── README.md

---

## Sources de donnees

| Source | Fichier brut | Fichier clean | Volume |
|--------|-------------|---------------|--------|
| Adzuna API | offres_idf.csv | offres_idf_clean.csv | 4 980 offres |
| France Travail API | offres_ft_idf.csv | offres_ft_idf_clean.csv | 24 051 offres |

---

## Pipeline - ordre de execution

# 1. Nettoyage donnees
python3 sources/clean_adzuna.py
python3 sources/clean_ft.py

# 2. Base de donnees
python3 sources/create_db.py

# 3. Mapping ROME et detection tensions
python3 sources/mapping_adzuna_rome.py

# 4. Analyse ML
python3 notebook/claire_analyse_tension.py

# 5. Dashboard
streamlit run webapp/app.py

---

## Resultats

- 55 metiers EN TENSION identifies
- 145 metiers LIBRES
- Modele ML : Random Forest
- Dashboard interactif sur http://localhost:8501

---

## Data Dictionnaire

| Champ | Source | Description | Risque qualite |
|-------|--------|-------------|----------------|
| code_rome | France Travail | Code metier 5 caracteres | - |
| titre | Adzuna / FT | Intitule du poste | Nettoyage requis |
| salaire_min | Adzuna | Salaire minimum annuel | 71% manquants |
| salaire_max | Adzuna | Salaire maximum annuel | 71% manquants |
| lieu | Adzuna / FT | Ville ou region | Normalisation requise |
| contrat | Adzuna / FT | CDI / CDD / Interim | Valeurs heterogenes |
| tension_itm | Calcule | EN TENSION / LIBRE | Seuil > 1.5 |

---

## Equipe et responsabilites

| Membre | Role | Taches |
|--------|------|--------|
| Claire | Data Analyst / ML | clean_adzuna.py, analyse_tension.py, dashboard |
| Bernard | Data Engineer | clean_ft.py, create_db.py, mapping_rome.py |

---

## Repo GitHub

https://github.com/maninconseil-commits/PPMT
