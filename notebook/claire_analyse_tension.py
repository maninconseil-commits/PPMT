# ============================================================
# NOTEBOOK ML - PREDICTION METIERS EN TENSION
# Claire - PPMT
# ============================================================

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
import warnings
warnings.filterwarnings("ignore")

print("=" * 60)
print("MODELE ML - PREDICTION INDICE DE TENSION METIERS")
print("=" * 60)

# ============================================================
# ETAPE 1 : CHARGEMENT
# ============================================================

print("\n--- ETAPE 1 : Chargement ---")

conn = sqlite3.connect("data/database.db")
df_itm = pd.read_sql("SELECT * FROM itm_consolide", conn)
df_ft = pd.read_sql("SELECT * FROM offres_ft_clean", conn)
try:
    df_adzuna = pd.read_sql("SELECT * FROM offres_adzuna_clean", conn)
except:
    df_adzuna = pd.read_csv("data/offres_idf_clean.csv")
conn.close()

print(f"ITM : {len(df_itm)} codes ROME")
print(f"Offres FT : {len(df_ft)}")
print(f"Offres Adzuna : {len(df_adzuna)}")

# ============================================================
# ETAPE 2 : FEATURE ENGINEERING
# ============================================================

# ETAPE 2 : FEATURE ENGINEERING
print("\n--- ETAPE 2 : Features ---")

# Agregation FT par code ROME
df_ft_agg = df_ft.groupby("code_rome").agg(
    nb_entreprises=("entreprise", "nunique"),
    nb_cdi=("contrat", lambda x: (x == "CDI").sum()),
    nb_cdd=("contrat", lambda x: (x == "CDD").sum()),
    nb_interim=("contrat", lambda x: (x.str.contains("Interim|interim", na=False)).sum()),
    desc_longueur_moy=("desc_longueur", "mean"),
    nb_departements=("departement", "nunique")
).reset_index()

df_ft_agg["pct_cdi"] = (df_ft_agg["nb_cdi"] / df_ft_agg["nb_cdi"].add(df_ft_agg["nb_cdd"]).replace(0,1) * 100).round(1)
df_ft_agg["pct_cdd"] = (df_ft_agg["nb_cdd"] / df_ft_agg["nb_cdi"].add(df_ft_agg["nb_cdd"]).replace(0,1) * 100).round(1)

# Fusion ITM + features FT
df_ml = df_itm.merge(df_ft_agg, on="code_rome", how="left")
df_ml = df_ml.dropna(subset=["nb_offres_total"])
print(f"Dataset ML : {df_ml.shape}")

# Fusion ITM + features FT
df_ml = df_itm.merge(df_ft_agg, on="code_rome", how="left")
df_ml = df_ml.dropna(subset=["nb_offres_total"])

print(f"Dataset ML apres merge : {df_ml.shape}")
print(f"Colonnes disponibles : {df_ml.columns.tolist()}")

# ============================================================
# ETAPE 3 : PREPARATION
# ============================================================

print("\n--- ETAPE 3 : Preparation ---")

FEATURES = [
    "nb_offres_ft",
    "nb_offres_adzuna",
    "nb_entreprises",
    "salaire_moyen_ft",
    "nb_cdi",
    "nb_cdd",
    "pct_cdi",
    "pct_cdd",
    "nb_departements",
    "desc_longueur_moy"
]

TARGET = "indice_tension"

df_model = df_ml[FEATURES + [TARGET, "code_rome", "libelle"]].dropna()
print(f"Lignes apres nettoyage NaN : {len(df_model)}")

X = df_model[FEATURES]
y = df_model[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print(f"Train : {len(X_train)} | Test : {len(X_test)}")

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================
# ETAPE 4 : ENTRAINEMENT
# ============================================================

print("\n--- ETAPE 4 : Entrainement ---")

modeles = {
    "Linear Regression": LinearRegression(),
    "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
    "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, random_state=42)
}

resultats = {}

for nom, modele in modeles.items():
    modele.fit(X_train_scaled, y_train)
    y_pred = modele.predict(X_test_scaled)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    mae = mean_absolute_error(y_test, y_pred)
    resultats[nom] = {"r2": r2, "rmse": rmse, "mae": mae, "modele": modele}
    print(f"{nom:25} | R2: {r2:.3f} | RMSE: {rmse:.1f} | MAE: {mae:.1f}")

# ============================================================
# ETAPE 5 : MEILLEUR MODELE
# ============================================================

print("\n--- ETAPE 5 : Meilleur modele ---")

meilleur_nom = max(resultats, key=lambda x: resultats[x]["r2"])
meilleur = resultats[meilleur_nom]
print(f"Meilleur modele : {meilleur_nom}")
print(f"R2 : {meilleur['r2']:.3f}")
print(f"RMSE : {meilleur['rmse']:.1f}")

# Importance features Random Forest
rf = resultats["Random Forest"]["modele"]
importances = pd.DataFrame({
    "feature": FEATURES,
    "importance": rf.feature_importances_
}).sort_values("importance", ascending=False)
print("\nImportance des features :")
print(importances.to_string())

# ============================================================
# ETAPE 6 : PREDICTIONS
# ============================================================

print("\n--- ETAPE 6 : Predictions ---")

meilleur_modele = meilleur["modele"]
df_model = df_model.copy()
df_model["itm_predit"] = meilleur_modele.predict(
    scaler.transform(df_model[FEATURES])
)
df_model["ecart"] = (df_model["itm_predit"] - df_model["indice_tension"]).abs()
df_model["statut_predit"] = df_model["itm_predit"].apply(
    lambda x: "TRES EN TENSION" if x > 150
    else "EN TENSION" if x > 100
    else "EQUILIBRE" if x > 50
    else "SATURE"
)

print("\nTop 10 metiers en tension predits :")
print(df_model.sort_values("itm_predit", ascending=False)[
    ["code_rome", "libelle", "indice_tension", "itm_predit", "statut_predit"]
].head(10).to_string())

# ============================================================
# ETAPE 7 : SAUVEGARDE
# ============================================================

print("\n--- ETAPE 7 : Sauvegarde ---")

os.makedirs("webapp/models", exist_ok=True)

joblib.dump(meilleur_modele, "webapp/models/modele_itm.pkl")
joblib.dump(scaler, "webapp/models/scaler_itm.pkl")
joblib.dump(FEATURES, "webapp/models/features_itm.pkl")

df_model.to_csv("data/predictions_itm.csv", index=False)

conn = sqlite3.connect("data/database.db")
df_model.to_sql("predictions_itm", conn, if_exists="replace", index=False)
conn.commit()
conn.close()

print(f"Modele : webapp/models/modele_itm.pkl")
print(f"Scaler : webapp/models/scaler_itm.pkl")
print(f"Predictions : data/predictions_itm.csv")

print("\n" + "=" * 60)
print("RAPPORT ML FINAL")
print("=" * 60)
print(f"Dataset : {len(df_model)} codes ROME")
print(f"Features : {len(FEATURES)}")
print(f"Meilleur modele : {meilleur_nom}")
print(f"R2 score : {meilleur['r2']:.3f}")
print(f"RMSE : {meilleur['rmse']:.1f}")
print(f"MAE : {meilleur['mae']:.1f}")
print("\nProchaine etape : integrer le modele dans Streamlit")