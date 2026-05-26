import pandas as pd
import re

REMAP = {
    r"ménage|ménagère|femme de ménage|nettoyage|entretien":    "Services à la personne",
    r"auxiliaire de vie|assistant.* de vie|aide.* vie":         "Services à la personne",
    r"nounou|baby.sit|garde d.enfant|puéricult":                "Petite enfance & garde",
    r"éducateur.* jeunes enfants|auxiliaire.*puéricult":        "Petite enfance & garde",
    r"immobilier|conseiller immo|agent immo|safti|promoteur":   "Immobilier",
    r"infirmier|chirurgien|dentiste|psychologue|médecin":       "Santé & médical",
    r"technicien.*maintenance|maintenance.*technicien":         "Maintenance industrielle",
    r"paysagiste|jardinier":                                    "Espaces verts & paysagisme",
    r"professeur|cours particulier|enseignant|formateur":       "Enseignement & formation",
    r"recrutement|ressources humaines|rh ":                     "RH & Recrutement",
    r"promoteur.*vente|conseiller.*vente|commercial":           "Commerce & Vente",
    r"soudeur|métallurgie|tôlier|chaudronnier":                 "Métallurgie & Soudure",
    r"opérateur.*production|agent.*production":                 "Opérateur de production",
    r"conducteur.*machine|régleur|usineur":                     "Conduite de machines",
    r"menuisier|charpentier|ébéniste":                          "Bois & Menuiserie",
    r"électricien|électrotechnicien":                           "Électricité & Électrotechnique",
    r"plombier|chauffagiste|sanitaire":                         "Plomberie & Chauffage",
    r"maçon|carreleur|couvreur|peintre.*bâtiment":              "Gros oeuvre & Finitions",
    # Ajouts v2
    r"employé polyvalent|équipier polyvalent":              "Commerce & Distribution",
    r"éducateur|educateur|éducatrice":                      "Petite enfance & garde",
    r"aide.domicile|aide à domicile":                       "Services à la personne",
    r"plongeur|poissonnier":                                "Hôtellerie & Restauration",
    r"aide.soignant|aide soignant":                         "Santé & médical",
    r"ergothérapeute|orthophoniste|diététicien":            "Santé & médical",
    r"cardiologue|stomatologue|manipulateur.*médic":        "Santé & médical",
    r"technicien préleveur|laboratoire":                    "Santé & médical",
    r"juriste|droit":                                       "Juridique",
    r"gestionnaire adv|gestionnaire de paie":               "Finance & Gestion",
    r"gestionnaire copropriété|copropriété":                "Immobilier",
    r"patrimoine|gestion.*patrimoine":                      "Finance & Gestion",
    r"controleur financier|contrôleur financier":           "Finance & Gestion",
    r"scrum master|référent applicatif":                    "Numérique & Tech",
    r"technicien sav":                                      "Maintenance industrielle",
    r"animateur.*événement|animateur event":                "Événementiel",
    r"manager|responsable.*magasin":                        "Management & Direction",
    r"ripeur":                                              "Services urbains",
    r"esthéticien|estheticien":                             "Coiffure & Esthétique",
    r"assistant.*direction|assistante.*direction":          "Administration",
    r"agent.*accueil|chargé.*accueil":                      "Administration",
    r"agent.*administration|assistant.*admin":              "Administration",
    r"designer|concepteur.*intérieur":                      "Design & Architecture",
}

def reclasser(row):
    titre = str(row["titre"]).lower()
    cat   = str(row.get("categorie", ""))
    if "Autres" not in cat and "Fabrication" not in cat:
        return cat
    for pattern, nouvelle_cat in REMAP.items():
        if re.search(pattern, titre, re.IGNORECASE):
            return nouvelle_cat
    return cat

if __name__ == "__main__":
    # Adzuna — a une colonne categorie
    fichier = "data/offres_idf_clean.csv"
    try:
        df = pd.read_csv(fichier)
        avant = df["categorie"].value_counts().get("Emplois Autres/Général", 0)
        df["categorie"] = df.apply(reclasser, axis=1)
        apres = df["categorie"].value_counts().get("Emplois Autres/Général", 0)
        df.to_csv(fichier, index=False)
        print(f"OK {fichier} — Autres: {avant} -> {apres}")
        print(df["categorie"].value_counts().head(15))
    except FileNotFoundError:
        print(f"Fichier non trouve: {fichier}")

    # France Travail — pas de categorie, on la cree depuis appellation_rome
    fichier_ft = "data/offres_ft_idf_clean.csv"
    try:
        df_ft = pd.read_csv(fichier_ft)
        df_ft["categorie"] = df_ft["appellation_rome"]
        df_ft.to_csv(fichier_ft, index=False)
        print(f"OK {fichier_ft} — colonne categorie creee depuis appellation_rome")
        print(df_ft["categorie"].value_counts().head(10))
    except FileNotFoundError:
        print(f"Fichier non trouve: {fichier_ft}")
