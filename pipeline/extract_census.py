#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""Phase 0 - Recensement Wikidata pour le globe historique.

Interroge le point d'acces SPARQL de Wikidata pour :
  1. compter les evenements disponibles par categorie et par palier
     d'importance (nombre de sitelinks Wikipedia) ;
  2. extraire un echantillon par categorie pour juger la qualite
     (labels FR, dates, coordonnees) ;
  3. produire un rapport markdown : out/rapport_phase0.md

Usage :
    uv run extract_census.py             # recensement + echantillons + rapport
    uv run extract_census.py --census    # comptages seulement
    uv run extract_census.py --samples   # echantillons seulement

Duree attendue : 5 a 20 minutes (pauses de politesse entre requetes,
certaines requetes lourdes peuvent expirer -- c'est signale dans le
rapport, pas bloquant).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "HistoireGlobe/0.1 (projet personnel de visualisation historique; python-requests)"
OUT = Path(__file__).resolve().parent / "out"
PAUSE = 2.0          # pause de politesse entre requetes (secondes)
TIERS = [100, 40, 15]  # paliers d'importance = nb minimal de sitelinks
DATE_MIN = '"-3000-01-01T00:00:00Z"^^xsd:dateTime'
SAMPLE_MIN_SL = 40
SAMPLE_LIMIT = 25

# ---------------------------------------------------------------------------
# Categories : chaque entree definit les motifs SPARQL liant ?item, ?date
# et (optionnellement) ?coord. "tiers" surcharge les paliers pour les
# categories trop volumineuses (ex. : personnages).
# ---------------------------------------------------------------------------
CATEGORIES = [
    {
        "id": "batailles",
        "label": "Batailles et sieges",
        "pattern": "?item wdt:P31/wdt:P279* wd:Q178561 .",
        "date": "?item wdt:P585 ?date .",
        "coord": "?item wdt:P625 ?coord .",
    },
    {
        "id": "guerres",
        "label": "Guerres et conflits",
        "pattern": "?item wdt:P31/wdt:P279* wd:Q198 .",
        "date": "?item (wdt:P580|wdt:P585) ?date .",
        "coord": "?item wdt:P625 ?coord .",
    },
    {
        "id": "personnages",
        "label": "Personnages (lieu et date de naissance)",
        "pattern": "?item wdt:P31 wd:Q5 .",
        "date": "?item wdt:P569 ?date .",
        "coord": "?item wdt:P19 ?lieu . ?lieu wdt:P625 ?coord .",
        "tiers": [100, 40, 25],
        "note": "palier bas releve a 25 sitelinks : ~12 M d'humains dans Wikidata, "
                "un seuil plus bas ferait exploser volume et temps de requete.",
    },
    {
        "id": "inventions",
        "label": "Inventions et decouvertes (P575)",
        "pattern": "",
        "date": "?item wdt:P575 ?date .",
        "coord": "?item wdt:P189 ?lieu . ?lieu wdt:P625 ?coord .",
        "note": "tout item portant une 'date de decouverte ou d'invention'.",
    },
    {
        "id": "oeuvres",
        "label": "Oeuvres majeures (litterature, peinture, musique, cinema)",
        "pattern": "VALUES ?cls { wd:Q7725634 wd:Q3305213 wd:Q2188189 wd:Q11424 } "
                   "?item wdt:P31 ?cls .",
        "date": "?item (wdt:P571|wdt:P577) ?date .",
        "coord": None,
        "note": "pas de coordonnees propres : seront rattachees au lieu de "
                "creation ou de naissance de l'auteur en phase 1.",
    },
    {
        "id": "traites",
        "label": "Traites et accords",
        "pattern": "?item wdt:P31/wdt:P279* wd:Q131569 .",
        "date": "?item (wdt:P585|wdt:P571) ?date .",
        "coord": "?item wdt:P625 ?coord .",
    },
    {
        "id": "etats",
        "label": "Naissances d'Etats et d'entites politiques",
        "pattern": "VALUES ?cls { wd:Q3024240 wd:Q6256 wd:Q3624078 } "
                   "?item wdt:P31 ?cls .",
        "date": "?item wdt:P571 ?date .",
        "coord": "?item wdt:P625 ?coord .",
    },
    {
        "id": "catastrophes",
        "label": "Catastrophes (naturelles et humaines)",
        "pattern": "?item wdt:P31/wdt:P279* wd:Q3839081 .",
        "date": "?item wdt:P585 ?date .",
        "coord": "?item wdt:P625 ?coord .",
    },
]

# ---------------------------------------------------------------------------


def sparql(query: str, timeout: int = 180) -> dict:
    """Execute une requete SPARQL avec retries et respect du rate limiting."""
    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            r = requests.get(
                ENDPOINT,
                params={"query": query, "format": "json"},
                headers={"User-Agent": USER_AGENT,
                         "Accept": "application/sparql-results+json"},
                timeout=timeout,
            )
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", "30"))
                print(f"    ... rate limit, pause {wait}s", flush=True)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < 3:
                wait = 10 * (attempt + 1)
                print(f"    ... erreur ({exc.__class__.__name__}), retry dans {wait}s",
                      flush=True)
                time.sleep(wait)
    raise RuntimeError(f"echec apres 4 tentatives : {last_exc}")


def census_query(cat: dict, min_sl: int) -> str:
    return f"""
SELECT (COUNT(DISTINCT ?item) AS ?c) WHERE {{
  {cat['pattern']}
  {cat['date']}
  FILTER(?date >= {DATE_MIN})
  ?item wikibase:sitelinks ?sl .
  FILTER(?sl >= {min_sl})
}}"""


def sample_query(cat: dict) -> str:
    coord_block = f"OPTIONAL {{ {cat['coord']} }}" if cat.get("coord") else ""
    return f"""
SELECT ?item ?itemLabel ?date ?coord ?sl WHERE {{
  {cat['pattern']}
  {cat['date']}
  FILTER(?date >= {DATE_MIN})
  {coord_block}
  ?item wikibase:sitelinks ?sl .
  FILTER(?sl >= {SAMPLE_MIN_SL})
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en". }}
}}
ORDER BY DESC(?sl)
LIMIT {SAMPLE_LIMIT}"""


def year_of(iso: str | None) -> int | None:
    """Extrait l'annee d'une date Wikidata (gere les annees negatives)."""
    if not iso:
        return None
    s = iso.lstrip("+")
    neg = s.startswith("-")
    if neg:
        s = s[1:]
    try:
        y = int(s.split("-")[0])
    except (ValueError, IndexError):
        return None
    return -y if neg else y


def run_census() -> dict:
    results: dict = {}
    for cat in CATEGORIES:
        tiers = cat.get("tiers", TIERS)
        results[cat["id"]] = {}
        for min_sl in tiers:
            label = f"{cat['id']} (sitelinks >= {min_sl})"
            print(f"[recensement] {label} ...", flush=True)
            try:
                data = sparql(census_query(cat, min_sl))
                count = int(data["results"]["bindings"][0]["c"]["value"])
                results[cat["id"]][min_sl] = count
                print(f"    -> {count}", flush=True)
            except Exception as exc:
                results[cat["id"]][min_sl] = f"ERREUR: {exc}"
                print(f"    -> ERREUR: {exc}", flush=True)
            time.sleep(PAUSE)
    return results


def run_samples() -> dict:
    samples: dict = {}
    for cat in CATEGORIES:
        print(f"[echantillon] {cat['id']} ...", flush=True)
        try:
            data = sparql(sample_query(cat))
            rows = []
            for b in data["results"]["bindings"]:
                rows.append({
                    "qid": b["item"]["value"].rsplit("/", 1)[-1],
                    "label": b.get("itemLabel", {}).get("value"),
                    "annee": year_of(b.get("date", {}).get("value")),
                    "coord": b.get("coord", {}).get("value"),
                    "sitelinks": int(b["sl"]["value"]),
                })
            samples[cat["id"]] = rows
            print(f"    -> {len(rows)} lignes", flush=True)
        except Exception as exc:
            samples[cat["id"]] = f"ERREUR: {exc}"
            print(f"    -> ERREUR: {exc}", flush=True)
        time.sleep(PAUSE)
    return samples


def fmt(v) -> str:
    if isinstance(v, int):
        return f"{v:,}".replace(",", " ")
    return "timeout/erreur" if isinstance(v, str) and v.startswith("ERREUR") else str(v)


def write_report(census: dict | None, samples: dict | None) -> Path:
    OUT.mkdir(exist_ok=True)
    lines = ["# Rapport phase 0 - Recensement Wikidata", ""]
    lines.append(f"Genere le {time.strftime('%Y-%m-%d %H:%M')}.")
    lines.append("")

    if census:
        lines.append("## Volumes par categorie et palier d'importance")
        lines.append("")
        lines.append("Palier = nombre minimal de versions linguistiques (sitelinks) "
                      "de l'article Wikipedia. T1 : visible des le globe entier ; "
                      "T3 : visible en zoom rapproche.")
        lines.append("")
        lines.append("| Categorie | T1 (>=100) | T2 (>=40) | T3 (palier bas) |")
        lines.append("|---|---|---|---|")
        total_t3 = 0
        for cat in CATEGORIES:
            row = census.get(cat["id"], {})
            tiers = cat.get("tiers", TIERS)
            vals = [row.get(t, "?") for t in tiers]
            t3 = vals[-1]
            if isinstance(t3, int):
                total_t3 += t3
            t3_label = fmt(t3) + (f" (>= {tiers[-1]})" if tiers[-1] != 15 else "")
            lines.append(f"| {cat['label']} | {fmt(vals[0])} | {fmt(vals[1])} | {t3_label} |")
        lines.append("")
        lines.append(f"**Total estime au palier bas : ~{fmt(total_t3)} evenements** "
                      "(hors categories en erreur).")
        lines.append("")
        notes = [c for c in CATEGORIES if c.get("note")]
        if notes:
            lines.append("Notes :")
            for c in notes:
                lines.append(f"- *{c['label']}* : {c['note']}")
            lines.append("")

    if samples:
        lines.append("## Echantillons (top sitelinks par categorie)")
        lines.append("")
        for cat in CATEGORIES:
            rows = samples.get(cat["id"])
            lines.append(f"### {cat['label']}")
            lines.append("")
            if isinstance(rows, str):
                lines.append(f"_{rows}_")
                lines.append("")
                continue
            lines.append("| Item | Annee | Coordonnees | Sitelinks |")
            lines.append("|---|---|---|---|")
            for r in rows[:15]:
                coord = "oui" if r["coord"] else "-"
                lines.append(f"| {r['label']} ({r['qid']}) | {r['annee']} | {coord} | {r['sitelinks']} |")
            with_coord = sum(1 for r in rows if r["coord"])
            with_label = sum(1 for r in rows if r["label"] and not r["label"].startswith("Q"))
            lines.append("")
            lines.append(f"Qualite sur l'echantillon : {with_coord}/{len(rows)} geolocalises, "
                          f"{with_label}/{len(rows)} avec label lisible.")
            lines.append("")

    report = OUT / "rapport_phase0.md"
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Recensement Wikidata (phase 0)")
    parser.add_argument("--census", action="store_true", help="comptages seulement")
    parser.add_argument("--samples", action="store_true", help="echantillons seulement")
    args = parser.parse_args()
    do_census = args.census or not args.samples
    do_samples = args.samples or not args.census

    OUT.mkdir(exist_ok=True)
    census = samples = None
    if do_census:
        census = run_census()
        (OUT / "census.json").write_text(json.dumps(census, indent=2), encoding="utf-8")
    if do_samples:
        samples = run_samples()
        (OUT / "samples.json").write_text(
            json.dumps(samples, indent=2, ensure_ascii=False), encoding="utf-8")

    report = write_report(census, samples)
    print(f"\nRapport ecrit : {report}")
    print("Fichiers bruts : out/census.json, out/samples.json")


if __name__ == "__main__":
    sys.exit(main())
