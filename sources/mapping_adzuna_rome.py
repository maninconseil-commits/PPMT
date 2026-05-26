import pandas as pd

df = pd.read_csv('data/offres_idf_clean.csv')

mapping = {
    'Emplois Informatique': 'M1805',
    'Emplois Soins de santé et infirmiers': 'J1502',
    'Santé & médical': 'J1101',
    'Emplois Comptabilité et Finance': 'M1202',
    'Emplois Enseignement': 'K2107',
    'Enseignement & formation': 'K2101',
    'Emplois Vente': 'D1402',
    'Emplois Ingénierie': 'H1206',
    'Emplois Fabrication': 'H2101',
    'Emplois Industrie et Construction': 'F1101',
    'Emplois Hospitalité et Restauration': 'G1401',
    'Emplois Distribution et Entrepôts': 'N1101',
    'Services à la personne': 'K1301',
    'Petite enfance & garde': 'K1202',
    'Formation & Alternance': 'K2101',
    'Management & Direction': 'M1402',
    'Emplois Immobilier': 'C1501',
    'Emplois RH et Recrutement': 'M1502',
    'Emplois RP, Publicité et Marketing': 'E1102',
    'Emplois Autres/Général': 'M1607',
}

df['code_rome'] = df['categorie'].map(mapping).fillna('M1607')

df.to_csv('data/offres_idf_clean.csv', index=False)
print(f"Codes ROME assignes : {df['code_rome'].nunique()} codes uniques")
print(df['code_rome'].value_counts().head(10))
