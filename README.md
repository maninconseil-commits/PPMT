# PPMT — Prédiction des Pénuries de Main-d'Œuvre par Territoire

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)](https://streamlit.io)
[![Random Forest](https://img.shields.io/badge/ML-Random%20Forest%20R²%3D0.9952-green)]()
[![RNCP](https://img.shields.io/badge/RNCP-37827BC01-orange)]()

**Équipe** : Claire DIOUF & Bernard GBOHOUGNON  
**Formation** : Data Analyst — RNCP37827BC01 — Artefact  
**Périmètre** : Île-de-France — Adzuna + France Travail  
**Soutenance** : 29 mai 2026

---

## 1. Présentation du Projet

PPMT est une plateforme de veille automatisée du marché du travail français. Elle combine des données d'offres d'emploi en temps réel et des statistiques institutionnelles pour **prédire les métiers en tension par territoire**.

**Problématique** : Comment identifier automatiquement les métiers en tension de recrutement en Île-de-France afin d'améliorer l'orientation des demandeurs d'emploi et anticiper les pénuries de compétences ?

**Cibles** : Cabinets de recrutement · Candidats · Conseillers France Travail · Décideurs RH

---

## 2. Architecture du Pipeline

```
C1 — Collecte          C2/C3 — Nettoyage         C4 — Stockage         C5 — Service
────────────────    ──────────────────────    ─────────────────    ─────────────────────
API Adzuna       →  clean_adzuna.py        →  SQLite              →  Streamlit Dashboard
API France Travail  clean_ft.py               database.db             6 onglets interactifs
extract_api_ft.py   remap_categories.py       itm_consolide.csv       Filtres sidebar
                    mapping_adzuna_rome.py     predictions_itm.csv     KPI cards
                                                                       Bubble map IDF
                         ML : notebook/ml_tests.py
                         Random Forest R²=0.9952 — modele_itm.pkl
```

---

## 3. Structure du Projet

```
PPMT/
├── data/                          # Non versionné (.gitignore)
│   ├── offres_idf.csv             # Brut Adzuna
│   ├── offres_ft_idf.csv          # Brut France Travail
│   ├── offres_idf_clean.csv       # Adzuna nettoyé (4 626 offres)
│   ├── offres_ft_idf_clean.csv    # FT nettoyé (24 051 offres)
│   ├── itm_consolide.csv          # 1 102 métiers consolidés
│   ├── predictions_itm.csv        # Prédictions ML (790 lignes)
│   └── database.db                # Base SQLite
├── sources/
│   ├── clean_adzuna.py            # Nettoyage Adzuna (C2)
│   ├── clean_ft.py                # Nettoyage France Travail (C2)
│   ├── create_db.py               # Création SQLite (C4)
│   ├── extract_api_ft.py          # API France Travail OAuth2 (C1)
│   ├── mapping_adzuna_rome.py     # Mapping codes ROME (C3)
│   └── remap_categories.py        # Reclassification catégories (C3)
├── notebook/
│   ├── ml_tests.py                # Comparatif 3 modèles ML + Random Forest
│   └── bernard_nettoyage.py       # Exploration données
├── webapp/
│   ├── app.py                     # Dashboard Streamlit 6 onglets (C5)
│   └── models/
│       ├── modele_itm.pkl         # Random Forest R²=0.9952
│       ├── scaler_itm.pkl
│       └── features_itm.pkl
├── docs/
│   ├── dictionnaire.md            # Dictionnaire des 4 datasets
│   └── soutenance/
│       └── PPMT_Soutenance_RNCP37827BC01.pptx
├── .env                           # Non versionné — clés API
├── README.md
└── requirements.txt
```

---

## 4. Datasets

| Fichier | Lignes | Description | Source |
|---------|--------|-------------|--------|
| `offres_idf_clean.csv` | 4 626 | Offres Adzuna nettoyées | API Adzuna |
| `offres_ft_idf_clean.csv` | 24 051 | Offres France Travail nettoyées | API FT OAuth2 |
| `itm_consolide.csv` | 1 102 | Dataset ML consolidé (ITM par métier) | Adzuna + FT |
| `predictions_itm.csv` | 790 | Prédictions Random Forest | ML pipeline |

**Seuils ITM** : SATURÉ <50 · ÉQUILIBRÉ 50-100 · EN TENSION 100-150 · TRÈS EN TENSION >150

---

## 5. Installation

```bash
git clone https://github.com/maninconseil-commits/PPMT.git
cd PPMT
pip install -r requirements.txt
```

Créer le fichier `.env` :
```
FT_CLIENT_ID=votre_client_id
FT_CLIENT_SECRET=votre_client_secret
ADZUNA_APP_ID=votre_app_id
ADZUNA_APP_KEY=votre_app_key
```

---

## 6. Requirements

```
pandas>=1.5
numpy>=1.23
requests>=2.28
scikit-learn>=1.1
xgboost>=1.7
joblib>=1.2
streamlit>=1.20
plotly>=5.10
python-dotenv>=0.21
matplotlib>=3.6
seaborn>=0.12
```

---

## 7. Lancement

### Pipeline complet (ordre obligatoire)

```bash
python3 sources/clean_adzuna.py
python3 sources/clean_ft.py
python3 sources/remap_categories.py
python3 sources/create_db.py
python3 sources/mapping_adzuna_rome.py
python3 notebook/ml_tests.py
```

### Dashboard

```bash
streamlit run webapp/app.py
```

Accès : http://localhost:8501

---

## 8. Modèle Machine Learning

| Modèle | MAE | R² | Décision |
|--------|-----|----|----------|
| Régression Linéaire | 0.02 | 1.0000 | ❌ ÉCARTÉ — data leakage |
| XGBoost | 2.72 | 0.9940 | Non retenu |
| **Random Forest** | **2.24** | **0.9952** | ✅ **RETENU** |

**Features** : `nb_offres_ft`, `nb_offres_adzuna`, `nb_offres_total`, `salaire_moyen_ft`, `salaire_moyen_adzuna`, `salaire_moyen`

**Data leakage détecté** : `nb_offres_total = nb_offres_ft + nb_offres_adzuna` — la régression linéaire trouve la combinaison exacte → R²=1.0 artificiel.

---

## 9. Dashboard Streamlit — 6 Onglets

| Onglet | Contenu |
|--------|---------|
| Vue d'ensemble | KPIs, répartition statuts ITM, Top 10 tension, offres mai 2026 |
| Secteurs | État actuel vs Prédictions, contrats FT et Adzuna |
| Compétences & Tech | Hard skills, Soft skills, Technologies émergentes |
| Formations & Recrutement | Niveaux requis, modalités, CDI/CDD Top 10 |
| Métiers en Tension | Statut actuel vs prédit, bubble map IDF, scatter ITM |
| Salaires | FT vs Adzuna par métier, par secteur, par département |

---

## 10. Résultats Clés

- **29 031** offres analysées (Adzuna + France Travail)
- **1 102** métiers identifiés en IDF
- **176** métiers TRÈS EN TENSION
- **8/10** du Top 10 BMO 2025 confirmés TRÈS EN TENSION

**Top 5 métiers en tension IDF** :
1. Soins infirmiers J1502 — ITM 2 885
2. Informatique/Dev M1805 — ITM 2 791
3. Immobilier C1504 — ITM 2 243
4. Aide ménagère K1304 — ITM 2 005
5. Aide sociale K1311 — ITM 1 575

---

## 11. Perspectives

- Intégration API France Travail Offres (accès partenaire)
- Modèle de série temporelle (LSTM / Prophet) pour prédictions 6-12 mois
- Déploiement Streamlit Cloud avec authentification
- Extension à d'autres régions françaises
- Pipeline MLOps (MLflow + Airflow)

---

## 12. Organisation du Projet

| Membre | Rôle | Responsabilités |
|--------|------|-----------------|
| Bernard | Data Analyst + Admin Git | Adzuna, SQLite, mapping ROME, GitHub |
| Claire | Data Analyst + ML | France Travail, API FT, Random Forest, Dashboard |

**Méthode** : Points matin/soir · Push Git quotidien · Branches par fonctionnalité · Pull Requests

---

## Compétences RNCP37827BC01

| Compétence | Livrable |
|-----------|----------|
| C1 — Collecte automatisée | `extract_api_ft.py` + API Adzuna |
| C2 — Préparation données | `clean_adzuna.py` + `clean_ft.py` |
| C3 — Agrégation | `mapping_adzuna_rome.py` + `remap_categories.py` |
| C4 — Base de données | `create_db.py` + `database.db` + `dictionnaire.md` |
| C5 — Service numérique | `webapp/app.py` — Dashboard Streamlit |

---

*Formation Data Analyst — RNCP37827BC01 — Artefact — 2026*  
*Repo : https://github.com/maninconseil-commits/PPMT*
