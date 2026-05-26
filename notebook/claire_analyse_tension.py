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

features = ['nb_offres_ft', 'nb_offres_adzuna', 'nb_offres_total', 'salaire_moyen_ft', 'salaire_moyen_adzuna', 'salaire_moyen']

X = df[features].fillna(0)
y = df['indice_tension']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

modeles = {
    'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
    'XGBoost': GradientBoostingRegressor(n_estimators=100, random_state=42),
    'Regression Lineaire': LinearRegression(),
}

resultats = []
for nom, modele in modeles.items():
    if nom == 'Regression Lineaire':
        modele.fit(X_train_scaled, y_train)
        y_pred = modele.predict(X_test_scaled)
    else:
        modele.fit(X_train, y_train)
        y_pred = modele.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    resultats.append({'Modele': nom, 'MAE': round(mae, 4), 'R2': round(r2, 4)})
    print(f"{nom:25s} -> MAE: {mae:.4f} | R2: {r2:.4f}")

print("\n--- COMPARATIF ---")
df_res = pd.DataFrame(resultats).sort_values('R2', ascending=False)
print(df_res.to_string(index=False))

os.makedirs('webapp/models', exist_ok=True)
joblib.dump(modeles['Random Forest'], 'webapp/models/modele_itm.pkl')
joblib.dump(scaler, 'webapp/models/scaler_itm.pkl')
print("\nModele Random Forest sauvegarde dans webapp/models/")
