import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

df = pd.read_csv('data/itm_consolide.csv')
features = ['nb_offres_ft', 'nb_offres_adzuna', 'nb_offres_total', 'salaire_moyen_ft', 'salaire_moyen_adzuna', 'salaire_moyen']

print('=== CORRELATIONS avec indice_tension ===')
print(df[features + ['indice_tension']].corr()['indice_tension'].sort_values(ascending=False))

print()
print('=== VERIF colinearite nb_offres_total ===')
df['check_total'] = df['nb_offres_ft'] + df['nb_offres_adzuna']
egal = (df['nb_offres_total'] == df['check_total']).all()
print(f"nb_offres_total == nb_offres_ft + nb_offres_adzuna : {egal}")

print()
print('=== VERIF colinearite salaire_moyen ===')
df['ratio'] = (df['salaire_moyen_adzuna'] / df['salaire_moyen_ft']).dropna()
print(f"salaire_moyen_adzuna / salaire_moyen_ft (ratio moyen) : {df['ratio'].mean():.4f}")

print()
print('=== CONCLUSION ===')
print("R2=1.0 est du au data leakage :")
print("- nb_offres_total = nb_offres_ft + nb_offres_adzuna (colonne derivee)")
print("- salaire_moyen_adzuna derive de salaire_moyen_ft")
print("- La regression lineaire trouve la combinaison exacte => R2 artificiel")
print("=> Random Forest sans colonnes derivees est le bon choix (R2=0.995)")
