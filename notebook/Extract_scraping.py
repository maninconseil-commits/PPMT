"""
extract_scrape.py — Version Script Python (.py) mise à jour
Lit le fichier 'tous_les_codes_rome.json' généré par votre premier script,
puis lance le scraping Indeed pour chaque intitulé de métier trouvé.

Usages possibles dans le terminal :
    python extract_scrape.py                 # Lance le scraping pour tous les métiers ROME
    python extract_scrape.py --test          # Mode test rapide (2 métiers seulement)
    python extract_scrape.py --metier "Data Analyst" --ville Paris
"""

import json
import time
import random
import logging
import argparse
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# ─── 1. Configuration du Logging & Dossiers ───────────────────────────────────
logging.basicConfig(
level=logging.INFO,
format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# En mode script .py, on cible le dossier parent par rapport à l'emplacement du fichier
RAW_DIR = Path(__file__).parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

VILLES_PAR_DEFAUT = ["Paris", "Lyon", "Bordeaux", "Toulouse", "Marseille"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.google.fr/",
}

# ─── 2. Chargement dynamique de TOUS les métiers ROME ──────────────────────────
def charger_tous_les_metiers_rome() -> list[str]:
    """Lit le fichier généré par France Travail pour en extraire les intitulés."""
    chemin_fichier = RAW_DIR / "tous_les_codes_rome.json"

    if not chemin_fichier.exists():
        log.error(f":x: Le fichier {chemin_fichier} est introuvable. "
                  "Exécutez d'abord le script 'extract_liste_rome.py' !")
        return []

    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            donnees_rome = json.load(f)

        liste_metiers = [fiche.get("libelle") for fiche in donnees_rome if fiche.get("libelle")]
        log.info(f":books: {len(liste_metiers)} métiers chargés depuis le référentiel France Travail.")
        return liste_metiers
    except Exception as e:
        log.error(f":x: Erreur lors de la lecture des codes ROME : {e}")
        return []

# ─── 3. Fonctions outils pour le Scraping ──────────────────────────────────────
def sleep_polite(min_s: float = 2.5, max_s: float = 5.0):
    """Pause aléatoire pour essayer de passer sous les radars des anti-robots."""
    time.sleep(random.uniform(min_s, max_s))

def get_page(url: str, session: requests.Session) -> BeautifulSoup | None:
    try:
        resp = session.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 403:
            log.warning(f":no_entry: 403 Forbidden (Anti-robot activé) sur : {url}")
            return None
        if resp.status_code == 429:
            log.warning(":double_vertical_bar: Rate limit (429), pause forcée de 20 secondes...")
            time.sleep(20)
            return None
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        log.error(f":x: Erreur réseau sur {url}: {e}")
        return None

# ─── 4. Parsing des cartes d'offres Indeed ────────────────────────────────────
def _parse_indeed_card(card: BeautifulSoup, metier: str, ville: str) -> dict | None:
    try:
        titre_el = card.select_one("h2.jobTitle span[title]") or card.select_one("h2.jobTitle") or card.select_one("[data-testid='job-title']")
        entreprise_el = card.select_one("[data-testid='company-name']") or card.select_one("span.companyName")
        salaire_el = card.select_one("[data-testid='attribute_snippet_testid']") or card.select_one("div.salary-snippet-container")

        if not titre_el and not_entreprise_el:
            return None

        full_text = card.get_text(" ").lower()
        teletravail = any(kw in full_text for kw in ["télétravail", "remote", "distanciel"])

        contrat = "CDI"
        if "cdd" in full_text: contrat = "CDD"
        elif "alternance" in full_text or "apprentissage" in full_text: contrat = "Alternance"
        elif "stage" in full_text: contrat = "Stage"

        return {
            "titre": titre_el.get_text(strip=True) if titre_el else "N/A",
            "entreprise": entreprise_el.get_text(strip=True) if entreprise_el else "N/A",
            "localisation": ville,
            "salaire_brut": salaire_el.get_text(strip=True) if salaire_el else None,
            "teletravail": teletravail,
            "contrat": contrat,
            "metier_rome": metier,
            "source": "Indeed Scraping",
            "date_extraction": datetime.now().isoformat(),
        }
    except Exception:
        return None

# ─── 5. Scraping Indeed (Offres & Salaires) ───────────────────────────────────
def scrape_indeed_offres(metier: str, ville: str, session: requests.Session) -> list[dict]:
    offres = []
    query = requests.utils.quote(metier)
    loc = requests.utils.quote(ville)
    url = f"https://fr.indeed.com/jobs?q={query}&l={loc}"

    soup = get_page(url, session)
    if soup is None:
        return offres

    cards = soup.select("div.job_seen_beacon") or soup.select("li.css-5lfssm") or soup.select("[data-jk]")
    for card in cards:
        offre = _parse_indeed_card(card, metier, ville)
        if offre:
            offres.append(offre)
    return offres

def scrape_indeed_salaires(metier: str, session: requests.Session) -> dict | None:
    query = requests.utils.quote(metier)
    url = f"https://fr.indeed.com/career/salaries?q={query}&l=France"

    soup = get_page(url, session)
    if soup is None:
        return None

    try:
        sal_el = soup.select_one("[data-testid='salary-median']") or soup.select_one("div.css-1kl7oov")
        if sal_el:
            return {
                "metier_rome": metier,
                "salaire_median_annuel": sal_el.get_text(strip=True),
                "source": "Indeed Salaires",
                "date_extraction": datetime.now().isoformat()
            }
    except Exception:
        pass
    return None

# ─── 6. Pipeline Principal d'Exécution ────────────────────────────────────────
def run_pipeline_scraping(metiers: list[str] = None, villes: list[str] = None, test_mode: bool = False):

    # Si aucun métier n'est fourni, on charge automatiquement TOUT le fichier des codes ROME
    if not metiers:
        metiers = charger_tous_les_metiers_rome()

    villes = villes or VILLES_PAR_DEFAUT

    if not metiers:
        log.error(":x: Aucune liste de métiers disponible pour lancer le scraping.")
        return

    # Si le mode test est activé, on restreint pour éviter d'être banni instantanément
    if test_mode:
        metiers = metiers[:2]
        villes = villes[:2]
        log.info(":test_tube: Mode Test activé : traitement réduit à 2 métiers et 2 villes.")

    session = requests.Session()
    session.headers.update(HEADERS)

    resultats = {
        "metadata": {
            "date_debut": datetime.now().isoformat(),
            "description": "Scraping Indeed basé sur les intitulés officiels du ROME",
            "total_metiers_vises": len(metiers)
        },
        "offres_indeed": [],
        "salaires_indeed": []
    }

    log.info(f":rocket: Début de la collecte Indeed pour {len(metiers)} métiers...")

    # IMPORTANT : Pour l'ensemble complet, rajoutez un slice si vous voulez faire par morceaux, ex: metiers[:50]
    for index, metier in enumerate(metiers):
        log.info(f":pushpin: [{index+1}/{len(metiers)}] Extraction : {metier}")

        # 1. Scraping du salaire
        salaire_info = scrape_indeed_salaires(metier, session)
        if salaire_info:
            resultats["salaires_indeed"].append(salaire_info)
        sleep_polite()

        # 2. Scraping des offres par ville
        for ville in villes:
            offres_trouvees = scrape_indeed_offres(metier, ville, session)
            if offres_trouvees:
                resultats["offres_indeed"].extend(offres_trouvees)
                log.info(f"   :round_pushpin: {ville} : +{len(offres_trouvees)} offres")
            sleep_polite()

    # 3. Sauvegarde finale
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    chemin_sortie = RAW_DIR / f"{ts}_enrichissement_indeed.json"

    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    log.info(f":checkered_flag: Scraping terminé ! Fichier enregistré : {chemin_sortie}")
    log.info(f":bar_chart: Offres collectées  : {len(resultats['offres_indeed'])}")
    log.info(f":bar_chart: Salaires collectés : {len(resultats['salaires_indeed'])}")

# ─── 7. Point d'entrée CLI (Interface Ligne de Commande) ──────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraping Indeed par codes ROME — PPMT")
    parser.add_argument("--metier", nargs="+", help="Métiers spécifiques à scraper (ex: --metier 'Data Analyst')")
    parser.add_argument("--ville", nargs="+", help="Villes spécifiques à cibler (ex: --ville Paris Lyon)")
    parser.add_argument("--test", action="store_true", help="Lance un test ultra-rapide sur 2 métiers")
    args = parser.parse_args()

    run_pipeline_scraping(
        metiers=args.metier,
        villes=args.ville,
        test_mode=args.test
    )