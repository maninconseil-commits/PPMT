import sqlite3
import pandas as pd
from datetime import datetime

conn = sqlite3.connect("data/database.db")
cursor = conn.cursor()

print("Creation des tables...")

cursor.execute("""
CREATE TABLE IF NOT EXISTS offres_adzuna (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT, entreprise TEXT, lieu TEXT, departement TEXT,
    salaire_min REAL, salaire_max REAL, salaire_moyen REAL,
    date_publication TEXT, contrat TEXT, categorie TEXT,
    description TEXT, url TEXT, date_import TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS offres_ft (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titre TEXT, code_rome TEXT, entreprise TEXT, lieu TEXT,
    departement TEXT, salaire_min REAL, salaire_max REAL,
    date_publication TEXT, contrat TEXT, description TEXT,
    url TEXT, date_import TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS metiers_tension (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code_rome TEXT, intitule TEXT,
    nb_offres_adzuna INTEGER, nb_offres_ft INTEGER,
    nb_offres_total INTEGER, salaire_moyen REAL,
    indice_tension REAL, region TEXT, date_calcul TEXT
)
""")

conn.commit()
print("Tables creees")

df = pd.read_csv("data/offres_idf_clean.csv")
df["date_import"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
df.to_sql("offres_adzuna", conn, if_exists="replace", index=False)
print(f"{len(df)} offres injectees dans offres_adzuna")

conn.close()
print("Base de donnees prete : data/database.db")