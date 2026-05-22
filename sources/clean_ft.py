import pandas as pd
import sqlite3
from datetime import datetime
import re

print("=" * 55)
print("NETTOYAGE DONNEES FRANCE TRAVAIL - PPMT")
print("=" * 55)

df = pd.read_csv("data/offres_ft_idf.csv")
print(f"\n[AVANT] {len(df):,} lignes")

# DOUBLONS
print("\n--- Doublons ---")
avant = len(df)
df = df.drop_duplicates(subset=["url"], keep="first")
df = df.drop_duplicates(subset=["titre", "entreprise", "lieu"], keep="last")
print(f"Supprimes : {avant - len(df):,}")

# TITRES
df["titre"] = df["titre"].str.strip().str.replace(r"\s+", " ", regex=True)
df["titre"] = df["titre"].str.replace(r"\s*[\(\-]?\s*[HhFf]\s*/\s*[HhFf]\s*[\)\-]?\s*$", "", regex=True).str.strip()
df = df[df["titre"].str.len() >= 3]

# ENTREPRISES
df["entreprise"] = df["entreprise"].fillna("Non renseigne").str.strip()
df["entreprise"] = df["entreprise"].replace(["N/A", "n/a", "NA", "-", ".", ""], "Non renseigne")

# SALAIRES
def extraire_salaire(libelle):
    if pd.isna(libelle) or libelle == "":
        return None, None
    nombres = re.findall(r"[\d]+(?:[.,]\d+)?", str(libelle))
    nombres = [float(n.replace(",", ".")) for n in nombres if float(n.replace(",", ".")) > 0]
    if len(nombres) >= 2:
        return min(nombres), max(nombres)
    elif len(nombres) == 1:
        return nombres[0], nombres[0]
    return None, None

df[["salaire_min", "salaire_max"]] = df["salaire"].apply(lambda x: pd.Series(extraire_salaire(x)))

def normaliser(val):
    if pd.isna(val): return val
    if val < 100: return val * 1820
    elif val < 5000: return val * 12
    return val

df["salaire_min"] = df["salaire_min"].apply(normaliser)
df["salaire_max"] = df["salaire_max"].apply(normaliser)
df.loc[df["salaire_min"] < 10000, "salaire_min"] = None
df.loc[df["salaire_max"] > 300000, "salaire_max"] = None
df["salaire_moyen"] = (df["salaire_min"] + df["salaire_max"]) / 2
print(f"\nSalaires valides : {df['salaire_moyen'].notna().sum():,}")

# CONTRATS
df["contrat"] = df["contrat"].fillna("Non renseigne")

# DATES
df["date_publication"] = pd.to_datetime(df["date_publication"], errors="coerce")
df["date_publication"] = df["date_publication"].dt.tz_localize(None)
df["is_recente"] = df["date_publication"] >= pd.Timestamp("2025-11-01")
df["age_jours"] = (pd.Timestamp.now() - df["date_publication"]).dt.days
df["annee"] = df["date_publication"].dt.year
df["mois"] = df["date_publication"].dt.month

# DEPARTEMENTS
dept_map = {"75":"Paris","77":"Seine-et-Marne (77)","78":"Yvelines (78)",
            "91":"Essonne (91)","92":"Hauts-de-Seine (92)","93":"Seine-Saint-Denis (93)",
            "94":"Val-de-Marne (94)","95":"Val-d'Oise (95)"}
df["departement"] = df["departement"].astype(str).map(dept_map).fillna("Ile-de-France")
print("\nDepartements :")
print(df["departement"].value_counts().to_string())

# DESCRIPTIONS
df["description"] = df["description"].fillna("").str.strip()
df["desc_longueur"] = df["description"].str.len()

# SAUVEGARDE
df_clean = df[[
    "titre", "code_rome", "appellation_rome", "entreprise",
    "lieu", "departement", "salaire_min", "salaire_max", "salaire_moyen",
    "date_publication", "annee", "mois", "age_jours", "is_recente",
    "contrat", "experience", "desc_longueur", "description", "url"
]]

df_clean.to_csv("data/offres_ft_idf_clean.csv", index=False, encoding="utf-8-sig")

conn = sqlite3.connect("data/database.db")
df_clean.to_sql("offres_ft_clean", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

print("\n" + "=" * 55)
print("RAPPORT FINAL")
print("=" * 55)
print(f"Lignes initiales      : 25,200")
print(f"Lignes apres nettoyage: {len(df_clean):,}")
print(f"Reduction             : {(1 - len(df_clean)/25200)*100:.1f}%")
print(f"Salaires valides      : {df_clean['salaire_moyen'].notna().sum():,}")
print(f"Offres recentes       : {df_clean['is_recente'].sum():,}")
print(f"Codes ROME uniques    : {df_clean['code_rome'].nunique():,}")
print(f"Fichier sauvegarde    : data/offres_ft_idf_clean.csv")
