
#valider la qualité du modèle ML, tester ses prédictions sur plusieurs exemples concrets, corriger les éventuelles incohérences et préparer une version plus fiable pour l’intégration finale dans le dashboard Streamlit. 

import pandas as pd
import pickle

from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score


# 1. Charger les données
df = pd.read_csv("data/itm_consolide.csv")
# 2. Créer une variable utile à partir du code ROME
df["domaine_rome"] = df["code_rome"].str[0]

# 3. Définir la cible
target = "statut"

# 4. Choisir les variables explicatives
features = [
    "nb_offres_adzuna",
    "salaire_moyen_adzuna",
    "nb_offres_ft",
    "salaire_moyen_ft",
    "nb_offres_total",
    "salaire_moyen",
    "libelle",
    "domaine_rome",
]

X = df[features]
y = df[target]

# 5. Colonnes numériques et catégorielles
numeric_features = [
    "nb_offres_adzuna",
    "salaire_moyen_adzuna",
    "nb_offres_ft",
    "salaire_moyen_ft",
    "nb_offres_total",
    "salaire_moyen",
]

categorical_features = [
    "libelle",
    "domaine_rome",
]

# 6. Préprocessing
numeric_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline(steps=[
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore"))
])

preprocessor = ColumnTransformer(transformers=[
    ("num", numeric_transformer, numeric_features),
    ("cat", categorical_transformer, categorical_features)
])

# 7. Modèle amélioré
model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    class_weight="balanced",
    min_samples_leaf=3
)

pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("model", model)
])

# 8. Split train/test
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# 9. Entraîner
pipeline.fit(X_train, y_train)

# 10. Tester
y_pred = pipeline.predict(X_test)

print("Accuracy :", accuracy_score(y_test, y_pred))
print("F1 macro :", f1_score(y_test, y_pred, average="macro"))
print()
print(classification_report(y_test, y_pred))
print(confusion_matrix(y_test, y_pred))

# 11. Sauvegarder le modèle
with open("model_itm.pkl", "wb") as file:
    pickle.dump(pipeline, file)

print("Modèle sauvegardé : model_itm.pkl")


examples = pd.DataFrame([
    {
        "nb_offres_adzuna": 10,
        "salaire_moyen_adzuna": 32000,
        "nb_offres_ft": 50,
        "salaire_moyen_ft": 30000,
        "nb_offres_total": 60,
        "salaire_moyen": 31000,
        "libelle": "Informatique",
        "domaine_rome": "M"
    },
    {
        "nb_offres_adzuna": 0,
        "salaire_moyen_adzuna": 0,
        "nb_offres_ft": 3,
        "salaire_moyen_ft": 25000,
        "nb_offres_total": 3,
        "salaire_moyen": 25000,
        "libelle": "Commerce",
        "domaine_rome": "D"
    }
])

predictions = pipeline.predict(examples)

for i, pred in enumerate(predictions):
    print(f"Exemple {i + 1} :", pred)