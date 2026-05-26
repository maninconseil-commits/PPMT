# PPMT - Plateforme Predictive des Metiers en Tension

> Projet Data Analyst - Soutenance 29/05/2026
> Equipe : Bernard | Claire

---

## Objectif

Identifier les metiers en tension sur le marche du travail francais en croisant
les donnees Adzuna et France Travail, et proposer une analyse predictive via
un dashboard interactif Streamlit.

---

## Structure du projet

PPMT/
├── data/
│   ├── raw/
│   │   └── tous_les_codes_rome.json     # Referentiel codes ROME 4.0
│   ├── processed/
│   ├── offres_idf.csv                   # Donnees brutes Adzuna
│   ├── offres_ft_idf.csv               # Donnees brutes France Travail
│   ├── offres_idf_clean.csv            # Adzuna nettoye (4 626 offres)
│   ├── offres_ft_idf_clean.csv         # France Travail nettoye (24 051 offres)
│   ├── itm_consolide.csv               # 1 102 metiers consolides
│   ├── predictions_itm.csv             # Predictions ML Random Forest
├── docs/
│   └── dictionnaire.md                  # Dictionnaire des donnees
│   └── database.db                      # Base SQLite
├── sources/
│   ├── clean_adzuna.py                  # Nettoyage donnees Adzuna
│   ├── clean_ft.py                      # Nettoyage donnees France Travail
│   ├── create_db.py                     # Creation base SQLite
│   ├── mapping_adzuna_rome.py           # Mapping categories vers codes ROME
│   ├── remap_categories.py              # Reclassification categories Adzuna
│   └── extract_api_ft.py               # Extraction API France Travail (OAuth2)
├── notebook/
│   ├── ml_tests.py                      # Comparatif 3 modeles ML + data leakage
│   └── bernard_nettoyage.py             # Scripts nettoyage Bernard
├── webapp/
│   ├── app.py                           # Dashboard Streamlit
│   └── models/
│       ├── modele_itm.pkl              # Modele ML Random Forest (R2=0.9952)
│       ├── scaler_itm.pkl              # Scaler normalisation
│       └── features_itm.pkl            # Features du modele
├── .env                                 # Cles API (non versionne)
├── .gitignore
├── requirements.txt
└── README.md

---

## Installation

git clone https://github.com/maninconseil-commits/PPMT.git
cd PPMT
pip install -r requirements.txt

Creer le fichier .env a la racine :
FT_CLIENT_ID=votre_client_id
FT_CLIENT_SECRET=votre_client_secret

Les cles sont disponibles sur https://francetravail.io apres creation d'un compte.

---

## Sources de donnees

| Source | Fichier brut | Fichier clean | Volume |
|--------|-------------|---------------|--------|
| Adzuna API | offres_idf.csv | offres_idf_clean.csv | 4 626 offres |
| France Travail API | offres_ft_idf.csv | offres_ft_idf_clean.csv | 24 051 offres |
| ITM Consolide | - | itm_consolide.csv | 1 102 metiers |

---

## Pipeline - ordre d'execution

# 1. Nettoyage donnees
python3 sources/clean_adzuna.py
python3 sources/clean_ft.py

# 2. Reclassification categories
python3 sources/remap_categories.py

# 3. Base de donnees
python3 sources/create_db.py

# 4. Mapping codes ROME
python3 sources/mapping_adzuna_rome.py

# 5. Tests ML
python3 notebook/ml_tests.py

# 6. Dashboard
streamlit run webapp/app.py

---

## Modele ML

| Modele | MAE | R2 | Decision |
|--------|-----|----|----------|
| Random Forest | 2.24 | 0.9952 | RETENU |
| XGBoost | 2.72 | 0.9940 | Non retenu |
| Regression Lineaire | 0.02 | 1.0000 | ECARTE (data leakage) |

La regression lineaire a ete ecartee car elle exploite nb_offres_total
qui est une combinaison exacte de nb_offres_ft + nb_offres_adzuna.

---

## Resultats

| Statut | Seuil ITM | Nb metiers |
|--------|-----------|------------|
| SATURE | < 50 | 723 |
| EQUILIBRE | 50 - 100 | 145 |
| EN TENSION | 100 - 150 | 55 |
| TRES EN TENSION | > 150 | 179 |

Top metiers en tension : Soins infirmiers (2885), Informatique (2791), Immobilier (2243)

---

## Data Dictionnaire

| Champ | Source | Description | Qualite |
|-------|--------|-------------|---------|
| code_rome | France Travail | Code metier ROME 4.0 | Complet |
| titre | Adzuna / FT | Intitule du poste | Nettoye |
| salaire_moyen | Adzuna / FT | Salaire annuel moyen | Enrichi via mediane FT |
| contrat | Adzuna / FT | CDI / CDD / Interim / Autre | Normalise 4 categories |
| indice_tension | Calcule | Nb offres pour 100 candidats | Via ITM France Travail |
| statut | Calcule | SATURE / EQUILIBRE / EN TENSION / TRES EN TENSION | Seuils 50/100/150 |

---

## Equipe

| Membre | Role | Taches principales |
|--------|------|--------------------|
| Claire | Data Analyst | Nettoyage Adzuna, reclassification categories, modeles ML, dashboard |
| Bernard | Data Analyst | Nettoyage France Travail, base de donnees, mapping ROME, API FT |

---

## Repo GitHub

https://github.com/maninconseil-commits/PPMT
