#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""Extraction complete des evenements Wikidata pour le globe historique.

Integre les enseignements de la phase 0 :
  - seuils de sitelinks propres a chaque categorie (Waterloo = 93 !) ;
  - decoupage temporel adaptatif avec bissection automatique en cas de
    timeout ou de tranche trop dense (indispensable pour les personnages) ;
  - deduplication (valeurs multiples de proprietes), sauf pour les Etats
    ou les dates multiples = refondations (Clovis 481, Verdun 843,
    Empire 1804) ;
  - labels avec repli fr,en,mul ;
  - coordonnees avec repli (P189 puis P625 de l'item pour les inventions) ;
  - hierarchie part-of (P361) pour batailles/guerres/catastrophes ;
  - titres d'articles Wikipedia FR et EN (pour la fenetre de detail).

Usage :
    uv run extract_events.py                  # tout extraire
    uv run extract_events.py --only batailles personnages
    uv run extract_events.py --skip personnages

Sorties : out/events/{categorie}.json + out/stats_extraction.md
Duree : de quelques minutes (petites categories) a 1-2 h (personnages).
Le script est reprenable : une categorie deja extraite est sautee
(supprimer son fichier out/events/*.json pour la relancer).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests

ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "HistoireGlobe/0.2 (projet personnel de visualisation historique; python-requests)"
OUT = Path(__file__).resolve().parent / "out" / "events"
YEAR_MIN, YEAR_MAX = -3000, 2027
SLICE_LIMIT = 20000     # au-dela, on bissecte la tranche
PAUSE = 1.5
QUERY_TIMEOUT = 120

# ---------------------------------------------------------------------------
# Categories. tiers = (seuil_T1, seuil_T2) ; min_sl = plancher d'extraction.
# Seuils calibres sur le recensement de la phase 0.
# ---------------------------------------------------------------------------
CATEGORIES = [
    {
        "id": "batailles", "label": "Batailles et sieges",
        "pattern": "?item wdt:P31/wdt:P279* wd:Q178561 .",
        "date": "?item wdt:P585 ?date .",
        "coord": "?item wdt:P625 ?coord .",
        "parent": True,
        "min_sl": 8, "tiers": (60, 30),
    },
    {
        "id": "guerres", "label": "Guerres et conflits",
        "pattern": "?item wdt:P31/wdt:P279* wd:Q198 .",
        "date": "?item (wdt:P580|wdt:P585) ?date .",
        "date_end": "?item wdt:P582 ?dateEnd .",
        "coord": "?item wdt:P625 ?coord .",
        "parent": True,
        "min_sl": 8, "tiers": (120, 50),
    },
    {
        "id": "personnages", "label": "Personnages (naissance)",
        "pattern": "?item wdt:P31 wd:Q5 .",
        "date": "?item wdt:P569 ?date .",
        "coord": "?item wdt:P19 ?lieu . ?lieu wdt:P625 ?coord .",
        "min_sl": 25, "tiers": (150, 60),
        "initial_slice": 200,   # tranches initiales fines : categorie massive
    },
    {
        "id": "inventions", "label": "Inventions et decouvertes",
        "pattern": "",
        "date": "?item wdt:P575 ?date .",
        "coord": "?item wdt:P189 ?lieu . ?lieu wdt:P625 ?coord .",
        "coord2": "?item wdt:P625 ?coord2 .",
        "min_sl": 15, "tiers": (150, 60),
        "initial_slice": 500,
    },
    {
        "id": "oeuvres", "label": "Oeuvres majeures",
        "pattern": "VALUES ?cls { wd:Q7725634 wd:Q3305213 wd:Q2188189 wd:Q11424 } "
                   "?item wdt:P31 ?cls .",
        "date": "?item (wdt:P571|wdt:P577) ?date .",
        "min_sl": 20, "tiers": (140, 60),
        "initial_slice": 500,
    },
    {
        "id": "traites", "label": "Traites et accords",
        "pattern": "?item wdt:P31/wdt:P279* wd:Q131569 .",
        "date": "?item (wdt:P585|wdt:P571) ?date .",
        "coord": "?item wdt:P625 ?coord .",
        "min_sl": 8, "tiers": (90, 40),
    },
    {
        "id": "etats", "label": "Naissances et refondations d'Etats",
        "pattern": "VALUES ?cls { wd:Q3024240 wd:Q6256 wd:Q3624078 } "
                   "?item wdt:P31 ?cls .",
        "date": "?item wdt:P571 ?date .",
        "coord": "?item wdt:P625 ?coord .",
        "min_sl": 10, "tiers": (250, 100),
        "keep_all_dates": True,   # refondations = evenements distincts
    },
    {
        "id": "catastrophes", "label": "Catastrophes",
        "pattern": "?item wdt:P31/wdt:P279* wd:Q3839081 .",
        "date": "?item wdt:P585 ?date .",
        "coord": "?item wdt:P625 ?coord .",
        "parent": True,
        "min_sl": 8, "tiers": (90, 40),
    },
]

# ---------------------------------------------------------------------------


def sparql(query: str, timeout: int = QUERY_TIMEOUT) -> dict:
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            r = requests.get(
                ENDPOINT,
                params={"query": query, "format": "json"},
                headers={"User-Agent": USER_AGENT,
                         "Accept": "application/sparql-results+json"},
                timeout=timeout + 10,
            )
            if r.status_code == 429:
                wait = int(r.headers.get("Retry-After", "30"))
                print(f"      rate limit, pause {wait}s", flush=True)
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(8 * (attempt + 1))
    raise TimeoutError(str(last_exc))


def dt(year: int) -> str:
    sign = "-" if year < 0 else ""
    return f'"{sign}{abs(year):04d}-01-01T00:00:00Z"^^xsd:dateTime'


def build_query(cat: dict, y0: int, y1: int) -> str:
    opt = []
    if cat.get("date_end"):
        opt.append(f"OPTIONAL {{ {cat['date_end']} }}")
    if cat.get("coord"):
        opt.append(f"OPTIONAL {{ {cat['coord']} }}")
    if cat.get("coord2"):
        opt.append(f"OPTIONAL {{ {cat['coord2']} }}")
    if cat.get("parent"):
        opt.append("OPTIONAL { ?item wdt:P361 ?parent . }")
    opt.append("OPTIONAL { ?fr schema:about ?item ; "
               "schema:isPartOf <https://fr.wikipedia.org/> . }")
    opt.append("OPTIONAL { ?en schema:about ?item ; "
               "schema:isPartOf <https://en.wikipedia.org/> . }")
    optional = "\n  ".join(opt)
    return f"""
SELECT ?item ?itemLabel ?date ?dateEnd ?coord ?coord2 ?sl ?parent ?fr ?en WHERE {{
  {cat['pattern']}
  {cat['date']}
  FILTER(?date >= {dt(y0)} && ?date < {dt(y1)})
  ?item wikibase:sitelinks ?sl .
  FILTER(?sl >= {cat['min_sl']})
  {optional}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "fr,en,mul". }}
}}
LIMIT {SLICE_LIMIT}"""


def year_of(iso: str | None) -> int | None:
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


def parse_point(wkt: str | None) -> tuple[float, float] | None:
    """'Point(lon lat)' -> (lon, lat)"""
    if not wkt or not wkt.startswith("Point("):
        return None
    try:
        lon, lat = wkt[6:-1].split()
        return round(float(lon), 4), round(float(lat), 4)
    except ValueError:
        return None


def wiki_title(url: str | None) -> str | None:
    if not url:
        return None
    return requests.utils.unquote(url.rsplit("/", 1)[-1]).replace("_", " ")


def parse_rows(bindings: list, cat: dict) -> list[dict]:
    rows = []
    for b in bindings:
        def v(k):
            return b.get(k, {}).get("value")
        year = year_of(v("date"))
        if year is None or not (YEAR_MIN <= year <= YEAR_MAX):
            continue
        coord = parse_point(v("coord")) or parse_point(v("coord2"))
        rows.append({
            "qid": v("item").rsplit("/", 1)[-1],
            "label": v("itemLabel"),
            "year": year,
            "year_end": year_of(v("dateEnd")),
            "coord": coord,
            "sl": int(v("sl")),
            "parent": v("parent").rsplit("/", 1)[-1] if v("parent") else None,
            "fr": wiki_title(v("fr")),
            "en": wiki_title(v("en")),
        })
    return rows


def harvest(cat: dict) -> tuple[list[dict], list[str]]:
    """Extrait toute la categorie par tranches temporelles adaptatives."""
    width = cat.get("initial_slice", YEAR_MAX - YEAR_MIN)
    stack: list[tuple[int, int]] = []
    y = YEAR_MIN
    while y < YEAR_MAX:
        stack.append((y, min(y + width, YEAR_MAX)))
        y += width
    stack.reverse()

    rows: list[dict] = []
    errors: list[str] = []
    while stack:
        y0, y1 = stack.pop()
        print(f"    tranche {y0} -> {y1} ...", end=" ", flush=True)
        try:
            data = sparql(build_query(cat, y0, y1))
            batch = data["results"]["bindings"]
            if len(batch) >= SLICE_LIMIT and y1 - y0 > 1:
                mid = (y0 + y1) // 2
                stack += [(mid, y1), (y0, mid)]
                print("trop dense, bissection")
            else:
                rows.extend(parse_rows(batch, cat))
                print(f"{len(batch)} lignes")
        except TimeoutError as exc:
            if y1 - y0 > 1:
                mid = (y0 + y1) // 2
                stack += [(mid, y1), (y0, mid)]
                print("timeout, bissection")
            else:
                errors.append(f"{y0}-{y1}: {exc}")
                print("timeout, tranche abandonnee")
        time.sleep(PAUSE)
    return rows, errors


def dedupe(rows: list[dict], cat: dict) -> list[dict]:
    """Fusionne les lignes du meme item (valeurs multiples de proprietes).

    Cle = qid, sauf keep_all_dates (Etats) ou cle = (qid, annee) :
    chaque refondation reste un evenement distinct.
    """
    merged: dict = {}
    for r in rows:
        key = (r["qid"], r["year"]) if cat.get("keep_all_dates") else r["qid"]
        cur = merged.get(key)
        if cur is None:
            merged[key] = r
            continue
        if r["year"] < cur["year"]:
            cur["year"] = r["year"]
        if r["year_end"] and (not cur["year_end"] or r["year_end"] > cur["year_end"]):
            cur["year_end"] = r["year_end"]
        for f in ("coord", "parent", "fr", "en", "label"):
            if not cur[f] and r[f]:
                cur[f] = r[f]
    return sorted(merged.values(), key=lambda r: (r["year"], -r["sl"]))


def assign_tier(rows: list[dict], cat: dict) -> None:
    t1, t2 = cat["tiers"]
    for r in rows:
        r["tier"] = 1 if r["sl"] >= t1 else 2 if r["sl"] >= t2 else 3


def extract_category(cat: dict) -> dict:
    out_file = OUT / f"{cat['id']}.json"
    if out_file.exists():
        data = json.loads(out_file.read_text(encoding="utf-8"))
        print(f"[{cat['id']}] deja extrait ({len(data['events'])} evts), saute")
        return {"id": cat["id"], "count": len(data["events"]), "skipped": True}

    print(f"[{cat['id']}] extraction ...", flush=True)
    t0 = time.time()
    rows, errors = harvest(cat)
    events = dedupe(rows, cat)
    assign_tier(events, cat)
    out_file.write_text(
        json.dumps({"category": cat["id"], "label": cat["label"],
                    "generated": time.strftime("%Y-%m-%d %H:%M"),
                    "events": events},
                   ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8")
    stats = {
        "id": cat["id"], "count": len(events),
        "geo": sum(1 for e in events if e["coord"]),
        "fr": sum(1 for e in events if e["fr"]),
        "t1": sum(1 for e in events if e["tier"] == 1),
        "t2": sum(1 for e in events if e["tier"] == 2),
        "duree_s": int(time.time() - t0),
        "errors": errors,
    }
    print(f"[{cat['id']}] {stats['count']} evts "
          f"({stats['geo']} geolocalises, {stats['fr']} avec article FR, "
          f"{len(errors)} tranches en erreur) en {stats['duree_s']}s")
    return stats


def write_stats(all_stats: list[dict]) -> Path:
    lines = ["# Statistiques d'extraction", "",
             f"Genere le {time.strftime('%Y-%m-%d %H:%M')}.", "",
             "| Categorie | Evenements | Geolocalises | Article FR | T1 | T2 | Tranches en erreur |",
             "|---|---|---|---|---|---|---|"]
    total = 0
    for s in all_stats:
        if s.get("skipped"):
            lines.append(f"| {s['id']} | {s['count']} | (deja extrait) | | | | |")
        else:
            lines.append(f"| {s['id']} | {s['count']} | {s['geo']} | {s['fr']} "
                         f"| {s['t1']} | {s['t2']} | {len(s['errors'])} |")
        total += s["count"]
    lines += ["", f"**Total : {total} evenements.**", ""]
    for s in all_stats:
        for e in s.get("errors", []):
            lines.append(f"- {s['id']} : tranche abandonnee {e}")
    path = OUT.parent / "stats_extraction.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Extraction Wikidata complete")
    parser.add_argument("--only", nargs="+", help="categories a extraire")
    parser.add_argument("--skip", nargs="+", default=[], help="categories a sauter")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    cats = [c for c in CATEGORIES
            if (not args.only or c["id"] in args.only)
            and c["id"] not in args.skip]
    all_stats = [extract_category(c) for c in cats]
    path = write_stats(all_stats)
    print(f"\nStatistiques : {path}")


if __name__ == "__main__":
    main()
