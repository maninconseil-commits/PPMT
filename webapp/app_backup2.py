import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
import subprocess
from collections import Counter

st.set_page_config(page_title="PPMT", page_icon="📊", layout="wide")

@st.cache_data
def load_adzuna():
    try:
        conn = sqlite3.connect("data/database.db")
        df = pd.read_sql("SELECT * FROM offres_adzuna_clean", conn)
        conn.close()
    except:
        df = pd.read_csv("data/offres_idf_clean.csv")
    df["salaire_moyen"] = pd.to_numeric(df.get("salaire_moyen"), errors="coerce")
    df["date_publication"] = pd.to_datetime(df.get("date_publication"), errors="coerce")
    return df

@st.cache_data
def load_ft():
    try:
        df = pd.read_csv("data/offres_ft_idf_clean.csv")
        df["salaire_moyen"] = pd.to_numeric(df.get("salaire_moyen"), errors="coerce")
        return df
    except:
        return pd.DataFrame()

@st.cache_data
def load_predictions():
    try:
        return pd.read_csv("data/predictions_itm.csv")
    except:
        return pd.DataFrame()

@st.cache_data
def load_itm():
    try:
        return pd.read_csv("data/itm_consolide.csv")
    except:
        return pd.DataFrame()

@st.cache_data
def extract_skills(df, col="description"):
    hard = ["python","sql","excel","power bi","tableau","machine learning","deep learning",
        "tensorflow","pytorch","scikit","pandas","numpy","spark","hadoop","aws","azure","gcp",
        "docker","kubernetes","git","api","java","javascript","react","angular","node",
        "scala","airflow","dbt","looker","snowflake","databricks","nlp","sap","salesforce"]
    soft = ["communication","autonomie","rigueur","organisation","travail en equipe",
        "adaptabilite","leadership","creativite","gestion de projet","analytique",
        "problem solving","esprit d analyse","initiative","polyvalence","relationnel",
        "pedagogie","negociation","curiosite","proactivite"]
    tech = ["intelligence artificielle","ia","llm","gpt","blockchain","iot","cloud",
        "devops","mlops","data lake","data mesh","streaming","temps reel","automatisation",
        "rpa","cybersecurite","microservices","api rest","graphql","no-code","low-code"]
    formations = ["bac+2","bac+3","bac+5","master","licence","bts","dut","ingenieur",
        "mba","doctorat","certification","formation","diplome","alternance","apprentissage"]
    texts = df[col].dropna().str.lower().str.cat(sep=" ")
    def count_kw(kw_list):
        return {kw: texts.count(kw) for kw in kw_list if texts.count(kw) > 0}
    return {"hard": count_kw(hard), "soft": count_kw(soft), "tech": count_kw(tech), "formations": count_kw(formations)}

def merge_skills(s1, s2, key):
    return dict((Counter(s1.get(key, {})) + Counter(s2.get(key, {}))).most_common(15))

col_titre, col_btn = st.columns([4, 1])
with col_titre:
    st.markdown("# Plateforme Predictive des Metiers en Tension")
    st.markdown("**Ile-de-France** | Sources : Adzuna + France Travail | Soutenance 29/05/2026")
with col_btn:
    st.markdown("###")
    if st.button("Rafraichir", type="primary"):
        with st.spinner("Mise a jour..."):
            subprocess.run(["python3", "sources/clean_adzuna.py"])
            subprocess.run(["python3", "sources/clean_ft.py"])
            subprocess.run(["python3", "sources/remap_categories.py"])
            subprocess.run(["python3", "sources/create_db.py"])
            subprocess.run(["python3", "sources/mapping_adzuna_rome.py"])
            subprocess.run(["python3", "notebook/ml_tests.py"])
            st.cache_data.clear()
        st.success("Donnees mises a jour !")
        st.rerun()

st.divider()
df_az = load_adzuna()
df_ft = load_ft()
df_pred = load_predictions()
df_itm = load_itm()
df_all = pd.concat([df_az, df_ft], ignore_index=True) if len(df_ft) > 0 else df_az

tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs(["Vue densemble","Secteurs","Competences","Formations","Metiers par Region","Salaires"])

with tab1:
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.metric("Offres Adzuna", f"{len(df_az):,}")
    k2.metric("Offres France Travail", f"{len(df_ft):,}")
    k3.metric("Total offres", f"{len(df_all):,}")
    k4.metric("Metiers analyses", f"{len(df_itm):,}")
    tres = len(df_pred[df_pred["statut_predit"]=="TRES EN TENSION"]) if len(df_pred)>0 else 0
    k5.metric("Metiers TRES EN TENSION", f"{tres}")
    st.divider()
    c1,c2 = st.columns(2)
    with c1:
        st.subheader("Repartition des statuts ITM")
        if len(df_pred)>0:
            df_s = df_pred["statut_predit"].value_counts().reset_index()
            df_s.columns = ["statut","nb"]
            fig = px.bar(df_s, x="statut", y="nb", color="statut",
                color_discrete_map={"TRES EN TENSION":"#C53030","EN TENSION":"#DD6B20","EQUILIBRE":"#38A169","SATURE":"#2B6CB0"})
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("Top 10 metiers en tension")
        if len(df_pred)>0:
            top10 = df_pred.sort_values("indice_tension",ascending=False).head(10)
            fig2 = px.bar(top10, x="indice_tension", y="libelle", orientation="h",
                color="indice_tension", color_continuous_scale=["#FED7D7","#C53030"])
            fig2.update_layout(height=400,showlegend=False,coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("Secteurs - Aujourd hui vs Demain")
    st.info("Aujourd hui = offres actuelles | Demain = metiers TRES EN TENSION (signal demande future)")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Aujourd hui - Offres par secteur")
        df_cat = df_all.groupby("categorie").size().reset_index(name="nb")
        df_cat = df_cat[~df_cat["categorie"].isin(["Unknown",""])].sort_values("nb",ascending=True).tail(15)
        fig = px.bar(df_cat, x="nb", y="categorie", orientation="h",
            color="nb", color_continuous_scale=["#EBF8FF","#003189"])
        fig.update_layout(height=500,showlegend=False,coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Demain - Secteurs les plus en tension")
        if len(df_pred)>0:
            tres_df = df_pred[df_pred["statut_predit"]=="TRES EN TENSION"].copy()
            tres_df["secteur"] = tres_df["libelle"].apply(lambda x: x.split("/")[0].strip()[:30] if pd.notna(x) else "Autre")
            df_demain = tres_df.groupby("secteur").agg(nb=("code_rome","count"),itm=("indice_tension","mean")).reset_index()
            df_demain = df_demain.sort_values("itm",ascending=True).tail(15)
            fig2 = px.bar(df_demain, x="itm", y="secteur", orientation="h",
                color="itm", color_continuous_scale=["#FFF5F5","#C53030"])
            fig2.update_layout(height=500,showlegend=False,coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)
    st.divider()
    st.subheader("Recence des offres - Offres recentes vs anciennes")
    if "mois" in df_all.columns:
        df_m = df_all.groupby(["annee","mois"]).size().reset_index(name="nb")
        df_m["periode"] = df_m["annee"].astype(str)+"-"+df_m["mois"].astype(str).str.zfill(2)
        fig3 = px.line(df_m.sort_values("periode"), x="periode", y="nb", markers=True, color_discrete_sequence=["#003189"])
        fig3.update_layout(height=300)
        st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.subheader("Competences et Technologies")
    with st.spinner("Analyse des descriptions..."):
        sk_az = extract_skills(df_az) if len(df_az)>0 else {}
        sk_ft = extract_skills(df_ft) if len(df_ft)>0 else {}
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Hard Skills les plus demandes")
        hard = merge_skills(sk_az,sk_ft,"hard")
        if hard:
            df_h = pd.DataFrame(list(hard.items()),columns=["skill","nb"]).sort_values("nb")
            fig = px.bar(df_h, x="nb", y="skill", orientation="h",
                color="nb", color_continuous_scale=["#EBF8FF","#003189"])
            fig.update_layout(height=450,showlegend=False,coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Soft Skills les plus demandes")
        soft = merge_skills(sk_az,sk_ft,"soft")
        if soft:
            df_so = pd.DataFrame(list(soft.items()),columns=["skill","nb"]).sort_values("nb")
            fig2 = px.bar(df_so, x="nb", y="skill", orientation="h",
                color="nb", color_continuous_scale=["#F0FFF4","#38A169"])
            fig2.update_layout(height=450,showlegend=False,coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)
    st.divider()
    st.markdown("#### Technologies emergentes et tendances")
    tech = merge_skills(sk_az,sk_ft,"tech")
    if tech:
        df_t = pd.DataFrame(list(tech.items()),columns=["tech","nb"]).sort_values("nb",ascending=False)
        fig3 = px.bar(df_t.sort_values("nb"), x="nb", y="tech", orientation="h",
            color="nb", color_continuous_scale=["#FFF5F5","#C53030"])
        fig3.update_layout(height=450, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

with tab4:
    st.subheader("Formations et Tendances Recrutement")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Niveaux de formation demandes")
        form = merge_skills(sk_az,sk_ft,"formations")
        if form:
            df_f = pd.DataFrame(list(form.items()),columns=["formation","nb"]).sort_values("nb")
            fig = px.bar(df_f, x="nb", y="formation", orientation="h",
                color="nb", color_continuous_scale=["#FFFAF0","#DD6B20"])
            fig.update_layout(height=400,showlegend=False,coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Types de contrats")
        df_co = df_all.groupby("contrat").size().reset_index(name="nb")
        df_co = df_co[df_co["contrat"]!="Non renseigne"].sort_values("nb",ascending=False)
        fig2 = px.bar(df_co, x="contrat", y="nb", color="contrat",
            color_discrete_sequence=["#003189","#3182CE","#63B3ED","#BEE3F8"])
        fig2.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    st.divider()
    c3,c4 = st.columns(2)
    with c3:
        st.markdown("#### CDI vs CDD metiers en tension")
        if len(df_pred)>0 and "pct_cdi" in df_pred.columns:
            df_cdi = df_pred[df_pred["statut_predit"].isin(["TRES EN TENSION","EN TENSION"])].sort_values("pct_cdi",ascending=False).head(12)
            fig3 = px.bar(df_cdi, x="libelle", y=["pct_cdi","pct_cdd"], barmode="stack",
                color_discrete_map={"pct_cdi":"#003189","pct_cdd":"#63B3ED"})
            fig3.update_layout(height=400,xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)
    with c4:
        st.markdown("#### Top metiers a fort potentiel demain")
        if len(df_pred)>0:
            td = df_pred[df_pred["statut_predit"]=="TRES EN TENSION"].sort_values("indice_tension",ascending=False).head(10)[["libelle","indice_tension","statut_predit"]]
            td.columns = ["Metier","Indice tension","Statut"]
            st.dataframe(td, use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Metiers en Tension par Departement IDF")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Aujourd hui - Offres par departement")
        if "departement" in df_all.columns:
            df_d = df_all.groupby("departement").size().reset_index(name="nb")
            df_d = df_d[df_d["departement"].notna()].sort_values("nb")
            fig = px.bar(df_d, x="nb", y="departement", orientation="h",
                color="nb", color_continuous_scale=["#EBF8FF","#003189"])
            fig.update_layout(height=400,showlegend=False,coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Demain - Statuts metiers")
        if len(df_pred)>0:
            df_s2 = df_pred.groupby("statut_predit").agg(nb=("code_rome","count")).reset_index()
            fig2 = px.bar(df_s2, x="statut_predit", y="nb", color="statut_predit",
                color_discrete_map={"TRES EN TENSION":"#C53030","EN TENSION":"#DD6B20","EQUILIBRE":"#38A169","SATURE":"#2B6CB0"})
            fig2.update_layout(height=400,showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)
    st.divider()
    st.markdown("#### Top 10 metiers en tension IDF")
    if len(df_pred)>0:
        tt = df_pred.sort_values("indice_tension",ascending=False).head(10)[["code_rome","libelle","indice_tension","statut_predit","nb_offres_ft","nb_offres_adzuna"]]
        tt.columns = ["Code ROME","Metier","Indice tension","Statut","Offres FT","Offres Adzuna"]
        st.dataframe(tt, use_container_width=True, hide_index=True)
    st.divider()
    st.markdown("#### Comparaison Top 10 ecole BMO 2025 vs Nos donnees IDF")
    df_comp = pd.DataFrame({
        "Code ROME":["F1602","I1601","K1302","H2912","H2902","I1304","J1502","J1507","G1602","N4101"],
        "Metier":["Couvreur/Charpentier","Carrossier Auto","Aide a domicile","Ouvrier Chaudronnerie","Conducteur Usinage","Technicien Maintenance","Aide-Soignant","Paramedical","Chef Cuisinier","Chauffeur PL"],
        "Taux diff BMO":["89%","88%","87%","86%","85%","84%","82%","82%","79%","76%"],
        "Notre statut IDF":["TRES EN TENSION","NON TROUVE IDF","TRES EN TENSION","EQUILIBRE","TRES EN TENSION","TRES EN TENSION","TRES EN TENSION","TRES EN TENSION","TRES EN TENSION","TRES EN TENSION"],
        "Notre ITM IDF":[810.4,None,499.4,61.4,282.4,961.9,2885.7,151.4,1334.4,577.1]
    })
    st.dataframe(df_comp, use_container_width=True, hide_index=True)

with tab6:
    st.subheader("Salaires par Categorie et Departement")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("#### Salaire moyen par secteur (Adzuna)")
        df_sc = df_az[df_az["salaire_moyen"].notna()&(df_az["categorie"]!="Unknown")]
        if len(df_sc)>0:
            df_sg = df_sc.groupby("categorie")["salaire_moyen"].mean().reset_index().sort_values("salaire_moyen",ascending=True)
            fig = px.bar(df_sg, x="salaire_moyen", y="categorie", orientation="h",
                color="salaire_moyen", color_continuous_scale=["#F0FFF4","#276749"])
            fig.update_layout(height=500,showlegend=False,coloraxis_showscale=False)
            fig.update_xaxes(tickformat=",.0f",ticksuffix=" EUR")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.markdown("#### Salaire moyen par departement")
        df_sd2 = df_all[df_all["salaire_moyen"].notna()]
        if len(df_sd2)>0:
            df_sd = df_sd2.groupby("departement")["salaire_moyen"].agg(["mean","count"]).reset_index()
            df_sd.columns = ["departement","salaire_moyen","nb"]
            df_sd = df_sd[df_sd["nb"]>=5].sort_values("salaire_moyen",ascending=True)
            fig2 = px.bar(df_sd, x="salaire_moyen", y="departement", orientation="h",
                color="salaire_moyen", color_continuous_scale=["#F0FFF4","#276749"])
            fig2.update_layout(height=400,showlegend=False,coloraxis_showscale=False)
            fig2.update_xaxes(tickformat=",.0f",ticksuffix=" EUR")
            st.plotly_chart(fig2, use_container_width=True)
    st.divider()
    c3,c4 = st.columns(2)
    with c3:
        st.markdown("#### Distribution des salaires")
        df_dist = df_az[(df_az["salaire_moyen"].notna())&(df_az["salaire_moyen"]>15000)&(df_az["salaire_moyen"]<150000)]
        if len(df_dist)>0:
            fig3 = px.histogram(df_dist, x="salaire_moyen", nbins=30, color_discrete_sequence=["#003189"])
            fig3.update_layout(height=300)
            fig3.update_xaxes(tickformat=",.0f",ticksuffix=" EUR")
            st.plotly_chart(fig3, use_container_width=True)
    with c4:
        st.markdown("#### Salaires metiers en tension")
        if len(df_itm)>0:
            df_si = df_itm[df_itm["salaire_moyen"].notna()].sort_values("salaire_moyen",ascending=False).head(15)
            fig4 = px.bar(df_si, x="salaire_moyen", y="libelle", orientation="h",
                color="salaire_moyen", color_continuous_scale=["#F0FFF4","#276749"])
            fig4.update_layout(height=450,showlegend=False,coloraxis_showscale=False)
            fig4.update_xaxes(tickformat=",.0f",ticksuffix=" EUR")
            st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.caption(f"PPMT | Adzuna + France Travail | Bernard et Claire | {datetime.now().strftime('%d/%m/%Y')}")
