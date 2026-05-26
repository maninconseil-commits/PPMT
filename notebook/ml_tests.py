import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import joblib
import os

df = pd.read_csv('data/itm_consolide.csv')
print(f"Dataset : {len(df)} lignes")

features_avec = ['nb_offres_ft', 'nb_offres_adzuna', 'nb_offres_total', 'salaire_moyen_ft', 'salaire_moyen_adzuna', 'salaire_moyen']
features_sans = ['nb_offres_ft', 'nb_offres_adzuna', 'salaire_moyen_ft', 'salaire_moyen_adzuna', 'salaire_moyen']
y = df['indice_tension']

print("\n=== ETAPE 1 : COMPARATIF 3 MODELES (avec toutes les features) ===")
X = df[features_avec].fillna(0)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

modeles = {
    'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
    'XGBoost': GradientBoostingRegressor(n_estimators=100, random_state=42),
    'Regression Lineaire': LinearRegression(),
}

for nom, modele in modeles.items():
    if nom == 'Regression Lineaire':
        modele.fit(X_train_s, y_train)
        y_pred = modele.predict(X_test_s)
    else:
        modele.fit(X_train, y_train)
        y_pred = modele.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"{nom:25s} -> MAE: {mae:.4f} | R2: {r2:.4f}")

print("\n=== ETAPE 2 : TEST SANS nb_offres_total (detection data leakage) ===")
for label, features in [('AVEC nb_offres_total', features_avec), ('SANS nb_offres_total', features_sans)]:
    X = df[features].fillna(0)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler2 = StandardScaler()
    X_train_s = scaler2.fit_transform(X_train)
    X_test_s = scaler2.transform(X_test)
    print(f"\n--- {label} ---")
    for nom, modele in [('Random Forest', RandomForestRegressor(n_estimators=100, random_state=42)),
                        ('XGBoost', GradientBoostingRegressor(n_estimators=100, random_state=42)),
                        ('Regression Lineaire', LinearRegression())]:
        if nom == 'Regression Lineaire':
            modele.fit(X_train_s, y_train)
            y_pred = modele.predict(X_test_s)
        else:
            modele.fit(X_train, y_train)
            y_pred = modele.predict(X_test)
        print(f"{nom:25s} -> MAE: {mean_absolute_error(y_test, y_pred):.4f} | R2: {r2_score(y_test, y_pred):.4f}")

print("\n=== ETAPE 3 : ANALYSE DATA LEAKAGE Regression Lineaire ===")
print("nb_offres_total == nb_offres_ft + nb_offres_adzuna ?")
df['check'] = df['nb_offres_ft'] + df['nb_offres_adzuna']
print(f"Resultat : {(df['nb_offres_total'] == df['check']).all()}")
print("=> Regression Lineaire ecartee definitivement - R2=1.0 artificiel")

print("\n=== ETAPE 4 : SAUVEGARDE RANDOM FOREST (modele retenu) ===")
X_final = df[features_avec].fillna(0)
X_train, X_test, y_train, y_test = train_test_split(X_final, y, test_size=0.2, random_state=42)
rf_final = RandomForestRegressor(n_estimators=100, random_state=42)
rf_final.fit(X_train, y_train)
y_pred = rf_final.predict(X_test)
print(f"Random Forest final -> MAE: {mean_absolute_error(y_test, y_pred):.4f} | R2: {r2_score(y_test, y_pred):.4f}")
os.makedirs('webapp/models', exist_ok=True)
joblib.dump(rf_final, 'webapp/models/modele_itm.pkl')
joblib.dump(scaler, 'webapp/models/scaler_itm.pkl')
print("Modele sauvegarde dans webapp/models/modele_itm.pkl")
