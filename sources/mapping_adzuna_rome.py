import sqlite3
import pandas as pd
from datetime import datetime

# ============================================================
# MAPPING CATEGORIES ADZUNA -> CODES ROME
# ============================================================

MAPPING = {
    "Emplois Informatique": "M1805",
    "Emplois Comptabilité et Finance": "M1202",
    "Emplois Soins de santé et infirmiers": "J1502",
    "Emplois RP, Publicité et Marketing": "E1103",
    "Emplois Ingénierie": "H1206",
    "Emplois Industrie et Construction": "F1602",
    "Emplois Hospitalité et Restauration": "G1602",
    "Emplois Distribution et Entrepôts": "N1103",
    "Emplois Vente": "D1505",
    "Emplois RH et Recrutement": "M1502",
    "Emplois Enseignement": "K2107",
    "Emplois Immobilier": "C1504",
    "Emplois Administration": "M1602",
    "Emplois Maintenance": "I1304",
    "Emplois Création et Design": "E1205",
    "Emplois Scientifiques et AQ": "H1502",
    "Emplois Services client": "M1703",
    "Emplois Travail social": "K1201",
    "Emplois Consultants": "M1402",
    "Emplois Fabrication": "H2909",
    "Emplois Droit": "K1901",
    "Emploi Aide ménagère et Nettoyage": "K1304",
    "Emplois Voyages": "G1401",
    "Emplois Énergie, pétrole et gaz": "H2301",
    "Emplois Diplômés": "M1402",
    "Emplois Autres/Général": None,
    "Unknown": None
}

LIBELLES_ROME = {
    "J1502": "Soins infirmiers",
    "M1805": "Informatique/Dev",
    "C1504": "Immobilier",
    "K1304": "Aide menagere/Nettoyage",
    "J1506": "Sante",
    "M1203": "Comptabilite",
    "K1311": "Aide sociale",
    "K2107": "Enseignement",
    "G1602": "Restauration/Cuisine",
    "K1303": "Services personne",
    "M1502": "RH/Recrutement",
    "H1206": "Ingenierie R&D",
    "D1505": "Commercial",
    "E1103": "Communication/Marketing",
    "F1602": "BTP/Construction",
    "N1103": "Logistique/Entrepot",
    "M1602": "Administration/Secretariat",
    "I1304": "Maintenance electronique",
    "E1205": "Design/Multimedia",
    "H1502": "Ingenierie production",
    "M1703": "Service client",
    "K1201": "Action sociale",
    "M1402": "Conseil/Consulting",
    "H2909": "Conduite installation",
    "K1901": "Droit/Juridique",
    "G1401": "Tourisme/Voyages",
    "H2301": "Energie/Petrole",
    "M1202": "Audit/Finance"
}

# ============================================================
# CONNEXION BASE
# ============================================================

conn = sqlite3.connect("data/database.db")

# ============================================================
# CHARGEMENT DONNEES ADZUNA
# ============================================================

try:
    df_adzuna = pd.read_sql("SELECT * FROM offres_adzuna_clean", conn)
    print(f"Adzuna clean : {len(df_adzuna)} offres")
except:
    df_adzuna = pd.read_csv("data/offres_idf_clean.csv")
    print(f"Adzuna CSV : {len(df_adzuna)} offres")

# ============================================================
# CHARGEMENT DONNEES FRANCE TRAVAIL CLEAN
# ============================================================

try:
    df_ft = pd.read_sql("SELECT * FROM offres_ft_clean", conn)
    has_ft = True
    print(f"FT clean : {len(df_ft)} offres")
except:
    try:
        df_ft = pd.read_sql("SELECT * FROM offres_ft", conn)
        has_ft = True
        print(f"FT brut : {len(df_ft)} offres")
    except:
        df_ft = pd.DataFrame()
        has_ft = False
        print("FT non disponible")

# ============================================================
# MAPPER ADZUNA -> ROME
# ============================================================

df_adzuna["code_rome"] = df_adzuna["categorie"].map(MAPPING)
nb_mappes = df_adzuna["code_rome"].notna().sum()
print(f"\nAdzuna mappees : {nb_mappes} / {len(df_adzuna)} ({nb_mappes/len(df_adzuna)*100:.1f}%)")

# ============================================================
# CALCUL TENSION PAR CODE ROME
# ============================================================

# Tension Adzuna
df_tension_adzuna = df_adzuna[df_adzuna["code_rome"].notna()].groupby("code_rome").agg(
    nb_offres_adzuna=("titre", "count"),
    salaire_moyen_adzuna=("salaire_moyen", "mean")
).reset_index()

# Tension FT
if has_ft:
    df_tension_ft = df_ft[df_ft["code_rome"].notna()].groupby("code_rome").agg(
        nb_offres_ft=("titre", "count"),
        salaire_moyen_ft=("salaire_moyen", "mean") if "salaire_moyen" in df_ft.columns else ("titre", "count")
    ).reset_index()

    df_tension = df_tension_adzuna.merge(df_tension_ft, on="code_rome", how="outer")
    df_tension["nb_offres_adzuna"] = df_tension["nb_offres_adzuna"].fillna(0)
    df_tension["nb_offres_ft"] = df_tension["nb_offres_ft"].fillna(0)
    df_tension["salaire_moyen_adzuna"] = df_tension["salaire_moyen_adzuna"].fillna(0)
else:
    df_tension = df_tension_adzuna.copy()
    df_tension["nb_offres_ft"] = 0
    df_tension["salaire_moyen_ft"] = None

# Total offres
df_tension["nb_offres_total"] = df_tension["nb_offres_adzuna"] + df_tension["nb_offres_ft"]

# Salaire moyen consolide
if "salaire_moyen_ft" in df_tension.columns:
    df_tension["salaire_moyen"] = df_tension[["salaire_moyen_adzuna", "salaire_moyen_ft"]].mean(axis=1)
else:
    df_tension["salaire_moyen"] = df_tension["salaire_moyen_adzuna"]

# ============================================================
# CALCUL ITM
# ============================================================

moyenne = df_tension["nb_offres_total"].mean()
df_tension["indice_tension"] = (df_tension["nb_offres_total"] / moyenne * 100).round(1)

df_tension["statut"] = df_tension["indice_tension"].apply(
    lambda x: "TRES EN TENSION" if x > 150
    else "EN TENSION" if x > 100
    else "EQUILIBRE" if x > 50
    else "SATURE"
)

# Libelles
df_tension["libelle"] = df_tension["code_rome"].map(LIBELLES_ROME).fillna("Autre metier")

# Source calcul
df_tension["source_calcul"] = "adzuna+ft" if has_ft else "adzuna_only"
df_tension["date_calcul"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ============================================================
# SAUVEGARDE
# ============================================================

df_tension.to_sql("itm_consolide", conn, if_exists="replace", index=False)
df_tension.to_csv("data/itm_consolide.csv", index=False)

conn.commit()
conn.close()

# ============================================================
# RAPPORT FINAL
# ============================================================

print(f"\nITM calcule pour {len(df_tension)} codes ROME")
print(f"Source : {'Adzuna + France Travail' if has_ft else 'Adzuna uniquement'}")

print(f"\nTop 15 metiers en tension :")
print(df_tension.sort_values("indice_tension", ascending=False)[
    ["code_rome", "libelle", "nb_offres_adzuna", "nb_offres_ft", "nb_offres_total", "indice_tension", "statut"]
].head(15).to_string())

print(f"\nRepartition statuts :")
print(df_tension["statut"].value_counts().to_string())

print(f"\nFichiers generes :")
print(f"  - data/itm_consolide.csv")
print(f"  - database.db -> table itm_consolide")