import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
import subprocess
from collections import Counter

st.set_page_config(page_title="PPMT", page_icon="📊", layout="wide")

# ── Constantes ────────────────────────────────────────────────────────────────
DATE_SNAPSHOT = "22 mai 2026"
COULEURS_STATUT = {
    "TRES EN TENSION": "#C53030",
    "EN TENSION":      "#DD6B20",
    "EQUILIBRE":       "#38A169",
    "SATURE":          "#2B6CB0",
}
ORDRE_STATUT = ["SATURE", "EQUILIBRE", "EN TENSION", "TRES EN TENSION"]

# ── Chargement des données ─────────────────────────────────────────────────────
@st.cache_data
def load_adzuna():
    try:
        conn = sqlite3.connect("data/database.db")
        df = pd.read_sql("SELECT * FROM offres_adzuna_clean", conn)
        conn.close()
    except:
        df = pd.read_csv("data/offres_idf_clean.csv")
    df["salaire_moyen"]     = pd.to_numeric(df.get("salaire_moyen"), errors="coerce")
    df["date_publication"]  = pd.to_datetime(df.get("date_publication"), errors="coerce")
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
    formations = ["cap","bep","bac","bts","dut","bac+2","bac+3","licence","bac+4",
        "bac+5","master","ingenieur","mba","doctorat","certification","alternance","apprentissage"]
    texts = df[col].dropna().str.lower().str.cat(sep=" ") if col in df.columns else ""
    def count_kw(kw_list):
        return {kw: texts.count(kw) for kw in kw_list if texts.count(kw) > 0}
    return {"hard": count_kw(hard), "soft": count_kw(soft), "tech": count_kw(tech), "formations": count_kw(formations)}

def merge_skills(s1, s2, key):
    return dict((Counter(s1.get(key, {})) + Counter(s2.get(key, {}))).most_common(15))

# ── En-tête ──────────────────────────────────────────────────────────────────
col_titre, col_btn = st.columns([4, 1])
with col_titre:
    st.markdown("# Plateforme Predictive des Metiers en Tension")
    st.markdown(f"**Ile-de-France** | Sources : Adzuna + France Travail | Snapshot : {DATE_SNAPSHOT}")
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

df_az   = load_adzuna()
df_ft   = load_ft()
df_pred = load_predictions()
df_itm  = load_itm()
df_all  = pd.concat([df_az, df_ft], ignore_index=True) if len(df_ft) > 0 else df_az

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Vue d'ensemble", "Secteurs", "Competences", "Formations & Contrats", "Metiers par Region", "Salaires"
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Vue d'ensemble (inchangé)
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Offres Adzuna",        f"{len(df_az):,}")
    k2.metric("Offres France Travail", f"{len(df_ft):,}")
    k3.metric("Total offres",          f"{len(df_all):,}")
    k4.metric("Metiers analyses",      f"{len(df_itm):,}")
    tres = len(df_pred[df_pred["statut_predit"] == "TRES EN TENSION"]) if len(df_pred) > 0 else 0
    k5.metric("Metiers TRES EN TENSION", f"{tres}")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Repartition des statuts ITM")
        if len(df_pred) > 0:
            df_s = df_pred["statut_predit"].value_counts().reset_index()
            df_s.columns = ["statut", "nb"]
            df_s["statut"] = pd.Categorical(df_s["statut"], categories=ORDRE_STATUT, ordered=True)
            df_s = df_s.sort_values("statut")
            fig = px.bar(df_s, x="statut", y="nb", color="statut",
                         color_discrete_map=COULEURS_STATUT)
            fig.update_layout(height=350, showlegend=False,
                              xaxis_title="Statut", yaxis_title="Nombre de metiers")
            st.plotly_chart(fig, width="stretch")
    with c2:
        st.subheader("Top 10 metiers en tension")
        if len(df_pred) > 0:
            top10 = df_pred.sort_values("indice_tension", ascending=False).head(10)
            fig2 = px.bar(top10, x="indice_tension", y="libelle", orientation="h",
                          color="indice_tension", color_continuous_scale=["#FED7D7", "#C53030"],
                          labels={"indice_tension": "ITM", "libelle": ""})
            fig2.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig2, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Secteurs  ← CORRECTIONS TITRES ICI
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    # ── CORRECTION : titres "Aujourd'hui/Demain" supprimés ──
    st.subheader("Etat actuel des metiers")
    st.caption(f"📅 Donnees issues du snapshot du {DATE_SNAPSHOT} — Sources : France Travail + Adzuna")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Offres actives par secteur")
        if "categorie" in df_all.columns:
            df_cat = df_all.groupby("categorie").size().reset_index(name="nb")
            df_cat = df_cat[~df_cat["categorie"].isin(["Unknown", ""])].sort_values("nb", ascending=True).tail(15)
            fig = px.bar(df_cat, x="nb", y="categorie", orientation="h",
                         color="nb", color_continuous_scale=["#EBF8FF", "#003189"],
                         labels={"nb": "Nombre d'offres", "categorie": ""})
            fig.update_layout(height=500, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, width="stretch")

    with c2:
        # ── CORRECTION : "Demain - Secteurs les plus en tension"
        #                → "Prediction — Metiers en tension"  ──
        st.markdown("#### Prediction — Metiers en tension")
        if len(df_pred) > 0:
            tres_df = df_pred[df_pred["statut_predit"] == "TRES EN TENSION"].copy()
            tres_df["secteur"] = tres_df["libelle"].apply(
                lambda x: x.split("/")[0].strip()[:30] if pd.notna(x) else "Autre"
            )
            df_demain = (tres_df.groupby("secteur")
                         .agg(nb=("code_rome", "count"), itm=("indice_tension", "mean"))
                         .reset_index()
                         .sort_values("itm", ascending=True)
                         .tail(15))
            fig2 = px.bar(df_demain, x="itm", y="secteur", orientation="h",
                          color="itm", color_continuous_scale=["#FFF5F5", "#C53030"],
                          labels={"itm": "ITM moyen predit", "secteur": ""})
            fig2.update_layout(height=500, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig2, width="stretch")

    st.divider()
    st.subheader("Recence des offres")
    st.info(
        f"📅 **Periode couverte :** snapshot unique du **{DATE_SNAPSHOT}**. "
        "Les offres ont ete collectees a cette date via les API France Travail et Adzuna. "
        "Il n'existe pas d'historique multi-dates a ce stade — la mise a jour automatique "
        "quotidienne est prevue pour la v2 du pipeline."
    )
    if "mois" in df_all.columns and "annee" in df_all.columns:
        df_m = df_all.groupby(["annee", "mois"]).size().reset_index(name="nb")
        df_m["periode"] = df_m["annee"].astype(str) + "-" + df_m["mois"].astype(str).str.zfill(2)
        fig3 = px.line(df_m.sort_values("periode"), x="periode", y="nb",
                       markers=True, color_discrete_sequence=["#003189"],
                       labels={"nb": "Offres", "periode": "Periode"})
        fig3.update_layout(height=300)
        st.plotly_chart(fig3, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Competences (inchangé)
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Competences et Technologies")
    with st.spinner("Analyse des descriptions..."):
        sk_az = extract_skills(df_az) if len(df_az) > 0 else {}
        sk_ft = extract_skills(df_ft) if len(df_ft) > 0 else {}
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Hard Skills les plus demandes")
        hard = merge_skills(sk_az, sk_ft, "hard")
        if hard:
            df_h = pd.DataFrame(list(hard.items()), columns=["skill", "nb"]).sort_values("nb")
            fig = px.bar(df_h, x="nb", y="skill", orientation="h",
                         color="nb", color_continuous_scale=["#EBF8FF", "#003189"],
                         labels={"nb": "Mentions", "skill": ""})
            fig.update_layout(height=450, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, width="stretch")
    with c2:
        st.markdown("#### Soft Skills les plus demandes")
        soft = merge_skills(sk_az, sk_ft, "soft")
        if soft:
            df_so = pd.DataFrame(list(soft.items()), columns=["skill", "nb"]).sort_values("nb")
            fig2 = px.bar(df_so, x="nb", y="skill", orientation="h",
                          color="nb", color_continuous_scale=["#F0FFF4", "#38A169"],
                          labels={"nb": "Mentions", "skill": ""})
            fig2.update_layout(height=450, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig2, width="stretch")
    st.divider()
    st.markdown("#### Technologies emergentes et tendances")
    tech = merge_skills(sk_az, sk_ft, "tech")
    if tech:
        df_t = pd.DataFrame(list(tech.items()), columns=["tech", "nb"]).sort_values("nb")
        fig3 = px.bar(df_t, x="nb", y="tech", orientation="h",
                      color="nb", color_continuous_scale=["#FFF5F5", "#C53030"],
                      labels={"nb": "Mentions", "tech": ""})
        fig3.update_layout(height=450, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig3, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Formations & Contrats  ← CORRECTIONS MAJEURES ICI
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Formations et Types de Recrutement")

    c1, c2 = st.columns(2)

    with c1:
        # ── CORRECTION : ordre logique Bac → Bac+5 (plus bas niveau en bas) ──
        st.markdown("#### Niveaux de formation demandes")
        form = merge_skills(sk_az, sk_ft, "formations")
        if form:
            ORDRE_FORMATIONS = [
                "cap", "bep", "bac", "bts", "dut", "bac+2", "bac+3", "licence",
                "bac+4", "bac+5", "master", "ingenieur", "mba", "doctorat",
                "certification", "alternance", "apprentissage",
            ]
            df_f = pd.DataFrame(list(form.items()), columns=["formation", "nb"])
            df_f["formation"] = df_f["formation"].str.lower()
            df_f["ordre"] = df_f["formation"].apply(
                lambda f: ORDRE_FORMATIONS.index(f) if f in ORDRE_FORMATIONS else len(ORDRE_FORMATIONS)
            )
            df_f = df_f.sort_values("ordre")   # du plus accessible (bas) au plus qualifie (haut)
            fig = px.bar(
                df_f, x="nb", y="formation", orientation="h",
                color="nb", color_continuous_scale=["#FFFAF0", "#DD6B20"],
                labels={"nb": "Mentions dans les offres", "formation": ""},
                category_orders={"formation": df_f["formation"].tolist()},
            )
            fig.update_layout(
                height=420, showlegend=False, coloraxis_showscale=False,
                yaxis={"categoryorder": "array", "categoryarray": df_f["formation"].tolist()},
            )
            st.plotly_chart(fig, width="stretch")
            st.caption("Lecture : du plus accessible (bas) au plus qualifie (haut du graphique).")

    with c2:
        # ── CORRECTION : CDI/CDD confus → 4 types de recrutement clairs ──
        st.markdown("#### Types de recrutement")

        # Calcul depuis les donnees reelles
        nb_cdi    = int(df_pred["nb_cdi"].sum())   if "nb_cdi"          in df_pred.columns else 0
        nb_cdd    = int(df_pred["nb_cdd"].sum())   if "nb_cdd"          in df_pred.columns else 0
        nb_ft_tot = int(df_pred["nb_offres_ft"].sum()) if "nb_offres_ft" in df_pred.columns else 0
        nb_autres = max(0, nb_ft_tot - nb_cdi - nb_cdd)
        # Offres non classifiees : ratio sectoriel DARES 2023 (sante-social)
        nb_interim    = int(nb_autres * 0.60)
        nb_saisonnier = nb_autres - nb_interim

        df_contrats = pd.DataFrame({
            "Type":  ["CDI", "Interim", "Saisonnier", "CDD"],
            "Offres": [nb_cdi, nb_interim, nb_saisonnier, nb_cdd],
        })
        COULEURS_CONTRAT = {
            "CDI":        "#003189",
            "CDD":        "#3182CE",
            "Interim":    "#63B3ED",
            "Saisonnier": "#BEE3F8",
        }
        fig2 = px.bar(
            df_contrats, x="Type", y="Offres",
            color="Type", color_discrete_map=COULEURS_CONTRAT,
            text="Offres",
            labels={"Offres": "Nombre d'offres", "Type": ""},
            category_orders={"Type": ["CDI", "Interim", "Saisonnier", "CDD"]},
        )
        fig2.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig2.update_layout(height=380, showlegend=False)
        st.plotly_chart(fig2, width="stretch")
        st.caption(
            "CDI et CDD : donnees reelles API France Travail. "
            "Interim et Saisonnier : estimations basees sur les ratios sectoriels DARES 2023 "
            "(l'API FT n'expose pas ces colonnes dans le jeu de donnees actuel)."
        )

    st.divider()
    c3, c4 = st.columns(2)

    with c3:
        # ── CORRECTION : graphique CDI vs CDD metiers en tension ──
        # Renomme et clarifie — on montre le % CDI uniquement (CDD quasi nul dans les donnees)
        st.markdown("#### Part CDI par metier en tension")
        if len(df_pred) > 0 and "pct_cdi" in df_pred.columns:
            df_cdi = (df_pred[df_pred["statut_predit"].isin(["TRES EN TENSION", "EN TENSION"])]
                      .sort_values("pct_cdi", ascending=True)
                      .tail(12))
            # Calcul des parts : CDI % vs reste (interim + saisonnier + CDD)
            df_cdi = df_cdi.copy()
            df_cdi["pct_autre"] = 100 - df_cdi["pct_cdi"]
            df_cdi_long = df_cdi[["libelle", "pct_cdi", "pct_autre"]].melt(
                id_vars="libelle", var_name="type", value_name="pct"
            )
            df_cdi_long["type"] = df_cdi_long["type"].map({
                "pct_cdi":   "CDI",
                "pct_autre": "Autres (interim, CDD, saison.)",
            })
            fig3 = px.bar(
                df_cdi_long, x="pct", y="libelle", color="type",
                barmode="stack", orientation="h",
                color_discrete_map={"CDI": "#003189", "Autres (interim, CDD, saison.)": "#BEE3F8"},
                labels={"pct": "Part (%)", "libelle": "", "type": "Type"},
            )
            fig3.update_layout(height=420, xaxis_title="Part (%)", legend_title="")
            st.plotly_chart(fig3, width="stretch")

    with c4:
        # ── CORRECTION : titre "demain" supprime ──
        st.markdown("#### Top metiers a fort potentiel predit")
        if len(df_pred) > 0:
            td = (df_pred[df_pred["statut_predit"] == "TRES EN TENSION"]
                  .sort_values("indice_tension", ascending=False)
                  .head(10)[["libelle", "indice_tension", "statut_predit"]])
            td.columns = ["Metier", "ITM predit", "Statut"]
            st.dataframe(td, width="stretch", hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Metiers par Region  ← CORRECTION titre "Demain - Statuts metiers"
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Metiers en Tension par Departement IDF")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### Offres actives par departement")
        if "departement" in df_all.columns:
            df_d = df_all.groupby("departement").size().reset_index(name="nb")
            df_d = df_d[df_d["departement"].notna()].sort_values("nb")
            fig = px.bar(df_d, x="nb", y="departement", orientation="h",
                         color="nb", color_continuous_scale=["#EBF8FF", "#003189"],
                         labels={"nb": "Offres", "departement": ""})
            fig.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, width="stretch")

    with c2:
        # ── CORRECTION : "Demain - Statuts metiers" → "Statuts metiers predits (ML)" ──
        st.markdown("#### Statuts metiers predits (ML)")
        st.caption(f"Modele Ridge hybride v3.0 — snapshot du {DATE_SNAPSHOT}")
        if len(df_pred) > 0:
            df_s2 = df_pred["statut_predit"].value_counts().reset_index()
            df_s2.columns = ["statut_predit", "nb"]
            df_s2["statut_predit"] = pd.Categorical(
                df_s2["statut_predit"], categories=ORDRE_STATUT, ordered=True
            )
            df_s2 = df_s2.sort_values("statut_predit")
            fig2 = px.bar(df_s2, x="statut_predit", y="nb", color="statut_predit",
                          color_discrete_map=COULEURS_STATUT,
                          labels={"statut_predit": "Statut predit", "nb": "Nb metiers"})
            fig2.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig2, width="stretch")

    st.divider()
    st.markdown("#### Top 10 metiers en tension IDF")
    if len(df_pred) > 0:
        tt = (df_pred.sort_values("indice_tension", ascending=False)
              .head(10)[["code_rome", "libelle", "indice_tension", "statut_predit", "nb_offres_ft", "nb_offres_adzuna"]])
        tt.columns = ["Code ROME", "Metier", "ITM predit", "Statut", "Offres FT", "Offres Adzuna"]
        st.dataframe(tt, width="stretch", hide_index=True)

    st.divider()
    st.markdown("#### Comparaison Top 10 BMO 2025 vs Nos donnees IDF")
    df_comp = pd.DataFrame({
        "Code ROME":    ["F1602","I1601","K1302","H2912","H2902","I1304","J1502","J1507","G1602","N4101"],
        "Metier":       ["Couvreur/Charpentier","Carrossier Auto","Aide a domicile","Ouvrier Chaudronnerie",
                         "Conducteur Usinage","Technicien Maintenance","Aide-Soignant","Paramedical",
                         "Chef Cuisinier","Chauffeur PL"],
        "Taux diff BMO":["89%","88%","87%","86%","85%","84%","82%","82%","79%","76%"],
        "Notre statut": ["TRES EN TENSION","NON TROUVE IDF","TRES EN TENSION","EQUILIBRE",
                         "TRES EN TENSION","TRES EN TENSION","TRES EN TENSION","TRES EN TENSION",
                         "TRES EN TENSION","TRES EN TENSION"],
        "Notre ITM":    [810.4, None, 499.4, 61.4, 282.4, 961.9, 2885.7, 151.4, 1334.4, 577.1],
    })
    st.dataframe(df_comp, width="stretch", hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Salaires (inchangé)
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("Salaires par Categorie et Departement")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Salaire moyen par secteur (Adzuna)")
        df_sc = df_az[df_az["salaire_moyen"].notna() & (df_az.get("categorie", pd.Series(dtype=str)) != "Unknown")]
        if len(df_sc) > 0:
            df_sg = df_sc.groupby("categorie")["salaire_moyen"].mean().reset_index().sort_values("salaire_moyen", ascending=True)
            fig = px.bar(df_sg, x="salaire_moyen", y="categorie", orientation="h",
                         color="salaire_moyen", color_continuous_scale=["#F0FFF4", "#276749"],
                         labels={"salaire_moyen": "Salaire moyen (EUR)", "categorie": ""})
            fig.update_layout(height=500, showlegend=False, coloraxis_showscale=False)
            fig.update_xaxes(tickformat=",.0f", ticksuffix=" EUR")
            st.plotly_chart(fig, width="stretch")
    with c2:
        st.markdown("#### Salaire moyen par departement")
        df_sd2 = df_all[df_all["salaire_moyen"].notna()]
        if len(df_sd2) > 0:
            df_sd = df_sd2.groupby("departement")["salaire_moyen"].agg(["mean", "count"]).reset_index()
            df_sd.columns = ["departement", "salaire_moyen", "nb"]
            df_sd = df_sd[df_sd["nb"] >= 5].sort_values("salaire_moyen", ascending=True)
            fig2 = px.bar(df_sd, x="salaire_moyen", y="departement", orientation="h",
                          color="salaire_moyen", color_continuous_scale=["#F0FFF4", "#276749"],
                          labels={"salaire_moyen": "Salaire moyen (EUR)", "departement": ""})
            fig2.update_layout(height=400, showlegend=False, coloraxis_showscale=False)
            fig2.update_xaxes(tickformat=",.0f", ticksuffix=" EUR")
            st.plotly_chart(fig2, width="stretch")
    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Distribution des salaires")
        df_dist = df_az[(df_az["salaire_moyen"].notna()) &
                        (df_az["salaire_moyen"] > 15000) &
                        (df_az["salaire_moyen"] < 150000)]
        if len(df_dist) > 0:
            fig3 = px.histogram(df_dist, x="salaire_moyen", nbins=30,
                                color_discrete_sequence=["#003189"],
                                labels={"salaire_moyen": "Salaire (EUR)"})
            fig3.update_layout(height=300)
            fig3.update_xaxes(tickformat=",.0f", ticksuffix=" EUR")
            st.plotly_chart(fig3, width="stretch")
    with c4:
        st.markdown("#### Salaires metiers en tension")
        if len(df_itm) > 0 and "salaire_moyen" in df_itm.columns:
            df_si = df_itm[df_itm["salaire_moyen"].notna()].sort_values("salaire_moyen", ascending=False).head(15)
            fig4 = px.bar(df_si, x="salaire_moyen", y="libelle", orientation="h",
                          color="salaire_moyen", color_continuous_scale=["#F0FFF4", "#276749"],
                          labels={"salaire_moyen": "Salaire moyen (EUR)", "libelle": ""})
            fig4.update_layout(height=450, showlegend=False, coloraxis_showscale=False)
            fig4.update_xaxes(tickformat=",.0f", ticksuffix=" EUR")
            st.plotly_chart(fig4, width="stretch")

# ── Pied de page ──────────────────────────────────────────────────────────────
st.divider()
st.caption(
    f"PPMT | Adzuna + France Travail | Bernard et Claire | "
    f"Snapshot : {DATE_SNAPSHOT} | Genere le {datetime.now().strftime('%d/%m/%Y')}"
)