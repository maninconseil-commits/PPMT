import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime
import subprocess

st.set_page_config(
    page_title="PPMT - Plateforme Predictive des Metiers en Tension",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data():
    try:
        conn = sqlite3.connect("data/database.db")
        df = pd.read_sql("SELECT * FROM offres_adzuna", conn)
        conn.close()
    except:
        df = pd.read_csv("data/offres_idf_clean.csv")
    df["salaire_moyen"] = pd.to_numeric(df.get("salaire_moyen"), errors="coerce")
    if "date" in df.columns:
        df = df.rename(columns={"date": "date_publication"})
    df["date_publication"] = pd.to_datetime(df.get("date_publication"), errors="coerce")
    df["entreprise"] = df.get("entreprise", "").fillna("Non renseigne")
    df["contrat"] = df.get("contrat", "").fillna("Non renseigne")
    return df

@st.cache_data
def load_predictions():
    try:
        return pd.read_csv("data/predictions_itm.csv")
    except:
        return pd.DataFrame()

# HEADER
col_titre, col_btn = st.columns([4, 1])
with col_titre:
    st.markdown("# Plateforme Predictive des Metiers en Tension")
    st.markdown("**Ile-de-France** | Sources : Adzuna + France Travail")
with col_btn:
    st.markdown("###")
    if st.button("Rafraichir les donnees", type="primary"):
        with st.spinner("Mise a jour en cours..."):
            subprocess.run(["python3", "sources/clean_adzuna.py"])
            subprocess.run(["python3", "sources/clean_ft.py"])
            subprocess.run(["python3", "sources/create_db.py"])
            subprocess.run(["python3", "sources/mapping_adzuna_rome.py"])
            subprocess.run(["python3", "notebook/claire_analyse_tension.py"])
            st.cache_data.clear()
        st.success("Donnees mises a jour !")
        st.rerun()

st.divider()

df = load_data()
df_pred = load_predictions()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Offres totales", f"{len(df):,}")
k2.metric("Secteurs", df["categorie"].nunique())
k3.metric("Entreprises", df["entreprise"].nunique())
sal = df["salaire_moyen"].mean()
k4.metric("Salaire moyen", f"{sal:,.0f} EUR" if sal > 0 else "N/D")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Offres par Secteur")
    df_cat = df.groupby("categorie").size().reset_index(name="nb")
    df_cat = df_cat[df_cat["categorie"] != "Unknown"].sort_values("nb")
    fig = px.bar(df_cat, x="nb", y="categorie", orientation="h",
                 color="nb", color_continuous_scale=["#EBF8FF","#003189"])
    fig.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
    st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("Offres par Departement")
    if "departement" in df.columns:
        df_dept = df.groupby("departement").size().reset_index(name="nb")
        fig2 = px.bar(df_dept.sort_values("nb"), x="nb", y="departement",
                      orientation="h", color="nb",
                      color_continuous_scale=["#EBF8FF","#003189"])
        fig2.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig2, width="stretch")

st.subheader("Salaires par Secteur")
df_sal = df[df["salaire_moyen"].notna() & (df["categorie"] != "Unknown")]
if len(df_sal) > 0:
    df_sg = df_sal.groupby("categorie")["salaire_moyen"].mean().reset_index()
    df_sg = df_sg.sort_values("salaire_moyen", ascending=False)
    fig3 = px.bar(df_sg, x="categorie", y="salaire_moyen",
                  color="salaire_moyen", color_continuous_scale=["#EBF8FF","#003189"])
    fig3.update_layout(height=300, coloraxis_showscale=False)
    st.plotly_chart(fig3, width="stretch")

st.divider()

st.subheader("Prediction ML - Indice de Tension Metiers")

if len(df_pred) > 0:
    col_ml1, col_ml2 = st.columns(2)

    with col_ml1:
        st.markdown("**Top 10 metiers en tension**")
        st.dataframe(
            df_pred.sort_values("itm_predit", ascending=False)[
                ["code_rome", "libelle", "indice_tension", "itm_predit", "statut_predit"]
            ].head(10),
            width="stretch"
        )

    with col_ml2:
        st.markdown("**Repartition des statuts**")
        df_statuts = df_pred["statut_predit"].value_counts().reset_index()
        df_statuts.columns = ["statut", "nb"]
        fig_ml = px.pie(
            df_statuts, values="nb", names="statut",
            color_discrete_map={
                "TRES EN TENSION": "#C53030",
                "EN TENSION": "#DD6B20",
                "EQUILIBRE": "#38A169",
                "SATURE": "#2B6CB0"
            }
        )
        st.plotly_chart(fig_ml, width="stretch")
else:
    st.info("Predictions ML non disponibles")

st.divider()

st.subheader("Offres")
recherche = st.text_input("Rechercher...")
df_table = df[df["titre"].str.contains(recherche, case=False, na=False)] if recherche else df
st.dataframe(
    df_table[["titre","entreprise","lieu","contrat","salaire_moyen","url"]].head(100),
    width="stretch",
    column_config={"url": st.column_config.LinkColumn("Lien")}
)

st.divider()
st.caption(f"PPMT | Donnees : Adzuna + France Travail | {datetime.now().strftime('%d/%m/%Y')}")
