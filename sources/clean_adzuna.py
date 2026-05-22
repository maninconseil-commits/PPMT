import pandas as pd
import sqlite3
import re
from datetime import datetime

print("=" * 55)
print("NETTOYAGE DONNÉES ADZUNA - PPMT")
print("=" * 55)

df = pd.read_csv("data/offres_idf.csv")
print(f"\n[AVANT] {len(df):,} lignes")

# ETAPE 1 : DOUBLONS
print("\n--- ETAPE 1 : Doublons ---")
avant = len(df)
df = df.drop_duplicates(subset=["url"], keep="first")
print(f"Doublons URL supprimés : {avant - len(df):,}")
avant2 = len(df)
df = df.drop_duplicates(subset=["titre", "entreprise", "lieu"], keep="last")
print(f"Doublons titre+entreprise+lieu supprimés : {avant2 - len(df):,}")
print(f"Lignes restantes : {len(df):,}")

# ETAPE 2 : TITRES
print("\n--- ETAPE 2 : Titres ---")
df["titre"] = df["titre"].str.strip()
df["titre"] = df["titre"].str.replace(r"\s+", " ", regex=True)
avant = len(df)
df = df[df["titre"].str.len() >= 3]
print(f"Titres trop courts supprimés : {avant - len(df)}")
df["titre_clean"] = df["titre"].str.replace(
    r"\s*[\(\-]?\s*[HhFf]\s*/\s*[HhFf]\s*[\)\-]?\s*$", "", regex=True
).str.strip()

# ETAPE 3 : ENTREPRISES
print("\n--- ETAPE 3 : Entreprises ---")
df["entreprise"] = df["entreprise"].fillna("Non renseigné")
df["entreprise"] = df["entreprise"].str.strip()
df["entreprise"] = df["entreprise"].replace(
    ["N/A", "n/a", "NA", "-", ".", "Unknown", "null"], "Non renseigné"
)

# ETAPE 4 : SALAIRES
print("\n--- ETAPE 4 : Salaires ---")
df["salaire_min"] = pd.to_numeric(df["salaire_min"], errors="coerce")
df["salaire_max"] = pd.to_numeric(df["salaire_max"], errors="coerce")

def normaliser_salaire_annuel(val):
    if pd.isna(val):
        return val
    if val < 100:
        return val * 1820
    elif val < 5000:
        return val * 12
    else:
        return val

df["salaire_min_norm"] = df["salaire_min"].apply(normaliser_salaire_annuel)
df["salaire_max_norm"] = df["salaire_max"].apply(normaliser_salaire_annuel)
df.loc[df["salaire_min_norm"] < 10000, "salaire_min_norm"] = None
df.loc[df["salaire_max_norm"] > 300000, "salaire_max_norm"] = None
df["salaire_moyen"] = (df["salaire_min_norm"] + df["salaire_max_norm"]) / 2
nb_sal = df["salaire_moyen"].notna().sum()
print(f"Offres avec salaire valide : {nb_sal:,} ({nb_sal/len(df)*100:.1f}%)")
print(f"Salaire moyen IDF : {df['salaire_moyen'].mean():,.0f}€/an")

# ETAPE 5 : CONTRATS
print("\n--- ETAPE 5 : Contrats ---")
df["contrat"] = df["contrat"].fillna("Non renseigné")
contrat_map = {
    "full_time": "Temps plein",
    "part_time": "Temps partiel",
    "contract": "CDD",
    "permanent": "CDI",
    "temporary": "Intérim",
    "Non renseigné": "Non renseigné"
}
df["contrat_clean"] = df["contrat"].map(contrat_map).fillna(df["contrat"])
print(df["contrat_clean"].value_counts().to_string())

# ETAPE 6 : DATES
print("\n--- ETAPE 6 : Dates ---")
df["date_publication"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
df["date_publication"] = df["date_publication"].dt.tz_localize(None)
date_limite = pd.Timestamp("2025-11-01")
df["is_recente"] = df["date_publication"] >= date_limite
df["age_jours"] = (pd.Timestamp.now() - df["date_publication"]).dt.days
df["annee"] = df["date_publication"].dt.year
df["mois"] = df["date_publication"].dt.month
df["semaine"] = df["date_publication"].dt.isocalendar().week.astype(int)
print(f"Offres récentes : {df['is_recente'].sum():,}")

# ETAPE 7 : LIEUX
print("\n--- ETAPE 7 : Départements ---")
def extraire_departement(lieu):
    lieu = str(lieu)
    if any(x in lieu for x in ["Paris", "75"]): return "Paris"
    elif any(x in lieu for x in ["Hauts-de-Seine", "Boulogne", "Courbevoie", "Nanterre", "Puteaux", "Montrouge", "Rueil", "La Défense", "Châtillon", "Le Plessis", "Saint-Cloud", "Antony"]): return "Hauts-de-Seine (92)"
    elif any(x in lieu for x in ["Seine-Saint-Denis", "Saint-Denis", "Saint-Ouen", "Drancy", "Montreuil"]): return "Seine-Saint-Denis (93)"
    elif any(x in lieu for x in ["Val-de-Marne", "Créteil", "Vincennes", "Vitry", "Ivry"]): return "Val-de-Marne (94)"
    elif any(x in lieu for x in ["Yvelines", "Versailles", "Rambouillet", "Mantes", "Saint-Germain"]): return "Yvelines (78)"
    elif any(x in lieu for x in ["Essonne", "Evry", "Corbeil", "Les Ulis", "Marcoussis", "Massy", "Palaiseau"]): return "Essonne (91)"
    elif any(x in lieu for x in ["Val-d'Oise", "Cergy", "Argenteuil", "Pontoise", "Sarcelles"]): return "Val-d'Oise (95)"
    elif any(x in lieu for x in ["Seine-et-Marne", "Meaux", "Melun", "Réau", "Combs"]): return "Seine-et-Marne (77)"
    else: return "Île-de-France (autre)"

df["departement"] = df["lieu"].apply(extraire_departement)
print(df["departement"].value_counts().to_string())

# ETAPE 8 : DESCRIPTIONS
print("\n--- ETAPE 8 : Descriptions ---")
df["description"] = df["description"].str.strip()
df["desc_longueur"] = df["description"].str.len()
print(f"Description moyenne : {df['desc_longueur'].mean():.0f} caractères")

# ETAPE 9 : CATEGORIES UNKNOWN
print("\n--- ETAPE 9 : Catégories ---")
KEYWORDS_CATEGORIE = {
    "Emplois Informatique": ["développeur", "developer", "data", "python", "java", "devops", "cloud", "cyber", "réseau", "IT", "informatique", "software", "web"],
    "Emplois Soins de santé et infirmiers": ["infirmier", "aide-soignant", "médecin", "pharmacien", "kiné", "auxiliaire de vie"],
    "Emplois Comptabilité et Finance": ["comptable", "finance", "auditeur", "contrôleur", "trésorier"],
    "Emplois RP, Publicité et Marketing": ["marketing", "communication", "SEO", "SEA", "community manager"],
    "Emplois Ingénierie": ["ingénieur", "engineer", "bureau d'études", "R&D", "mécanique"],
    "Emplois Hospitalité et Restauration": ["chef", "cuisinier", "serveur", "barman", "restaurant", "hôtel"],
    "Emplois RH et Recrutement": ["RH", "ressources humaines", "recruteur", "talent"],
    "Emplois Vente": ["commercial", "vendeur", "business developer"],
    "Emplois Distribution et Entrepôts": ["logistique", "magasinier", "préparateur", "cariste", "supply chain"],
}

def reclassifier(row):
    if row["categorie"] != "Unknown":
        return row["categorie"]
    titre_lower = str(row["titre"]).lower()
    for categorie, keywords in KEYWORDS_CATEGORIE.items():
        if any(kw.lower() in titre_lower for kw in keywords):
            return categorie
    return "Emplois Autres/Général"

df["categorie_clean"] = df.apply(reclassifier, axis=1)
nb_reclassifies = ((df["categorie"] == "Unknown") & (df["categorie_clean"] != "Emplois Autres/Général")).sum()
print(f"Offres reclassifiées : {nb_reclassifies:,}")

# ETAPE 10 : SAUVEGARDE
print("\n--- ETAPE 10 : Sauvegarde ---")
df_clean = df[[
    "titre_clean", "entreprise", "lieu", "departement",
    "salaire_min_norm", "salaire_max_norm", "salaire_moyen",
    "date_publication", "annee", "mois", "semaine", "age_jours",
    "is_recente", "contrat_clean", "categorie_clean",
    "desc_longueur", "description", "url"
]].rename(columns={
    "titre_clean": "titre",
    "salaire_min_norm": "salaire_min",
    "salaire_max_norm": "salaire_max",
    "contrat_clean": "contrat",
    "categorie_clean": "categorie"
})

df_clean.to_csv("data/offres_idf_clean.csv", index=False, encoding="utf-8-sig")
conn = sqlite3.connect("data/database.db")
df_clean.to_sql("offres_adzuna_clean", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

print("\n" + "=" * 55)
print("RAPPORT FINAL")
print("=" * 55)
print(f"Lignes initiales      : 12,500")
print(f"Lignes après nettoyage: {len(df_clean):,}")
print(f"Réduction             : {(1 - len(df_clean)/12500)*100:.1f}%")
print(f"Salaires valides      : {df_clean['salaire_moyen'].notna().sum():,}")
print(f"Offres récentes       : {df_clean['is_recente'].sum():,}")
print(f"Fichier sauvegardé    : data/offres_idf_clean.csv")