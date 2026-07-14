#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Consolide les extractions Wikidata vers le dossier web/data.

- trie les evenements par annee (indispensable pour l'index temporel du front) ;
- copie chaque categorie dans web/data/{id}.json ;
- ecrit web/data/manifest.json (liste des categories disponibles) ;
- recalcule les statistiques globales de TOUTES les categories
  (contrairement a stats_extraction.md qui ne couvre que le dernier run).

Usage :  uv run build_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "out" / "events"
DST = HERE.parent / "web" / "data"

LABELS = {
    "batailles": "Batailles et sièges",
    "guerres": "Guerres et conflits",
    "personnages": "Personnages",
    "inventions": "Inventions et découvertes",
    "oeuvres": "Œuvres majeures",
    "traites": "Traités et accords",
    "etats": "États et régimes",
    "catastrophes": "Catastrophes",
}

# ---------------------------------------------------------------------------
# Correction du biais de notoriete recente : Wikipedia sur-represente la
# culture pop des 20e-21e siecles (footballeurs, chanteurs...). On deflate
# le score sitelinks des evenements recents avant de recalculer les paliers,
# et on elague sous le plancher. Napoleon n'est pas touche ; un footballeur
# a 30 sitelinks descend a 12 et sort du jeu.
# Format : liste de (annee_a_partir_de, facteur), du plus ancien au plus recent.
DEFLATION = {
    "personnages": [(1800, 0.8), (1900, 0.6), (1950, 0.4)],
    "oeuvres": [(1900, 0.7), (1950, 0.5)],
}
# seuils T1/T2 (dupliques d'extract_events.py -- garder synchronises)
TIERS = {
    "batailles": (60, 30), "guerres": (120, 50), "personnages": (150, 60),
    "inventions": (150, 60), "oeuvres": (140, 60), "traites": (90, 40),
    "etats": (250, 100), "catastrophes": (90, 40),
}
PLANCHERS = {"personnages": 25, "oeuvres": 20}


def sl_effectif(cat_id: str, e: dict) -> float:
    facteur = 1.0
    for annee, f in DEFLATION.get(cat_id, []):
        if e["year"] >= annee:
            facteur = f
    return e["sl"] * facteur


def recalibrer(cat_id: str, events: list[dict]) -> tuple[list[dict], int]:
    """Applique la deflation, recalcule les paliers, elague sous le plancher."""
    plancher = PLANCHERS.get(cat_id, 0)
    t1, t2 = TIERS.get(cat_id, (10**9, 10**9))
    gardes = []
    for e in events:
        sl_eff = sl_effectif(cat_id, e)
        if sl_eff < plancher:
            continue
        if cat_id in TIERS:
            e["tier"] = 1 if sl_eff >= t1 else 2 if sl_eff >= t2 else 3
        gardes.append(e)
    return gardes, len(events) - len(gardes)


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Aucune extraction trouvée dans {SRC} — lancer extract_events.py d'abord.")
    DST.mkdir(parents=True, exist_ok=True)

    manifest = []
    print(f"{'Catégorie':<14} {'Évts':>7} {'Élagués':>8} {'Géo':>7} {'FR':>7} {'T1':>5} {'T2':>6} {'T3':>7}")
    total = geo_total = 0
    for f in sorted(SRC.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        cat_id = data["category"]
        events, elagues = recalibrer(cat_id, data["events"])
        events = sorted(events, key=lambda e: (e["year"], -e["sl"]))
        out = {
            "category": cat_id,
            "label": LABELS.get(cat_id, data.get("label", cat_id)),
            "events": events,
        }
        (DST / f"{cat_id}.json").write_text(
            json.dumps(out, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
        geo = sum(1 for e in events if e["coord"])
        fr = sum(1 for e in events if e["fr"])
        t = [sum(1 for e in events if e["tier"] == i) for i in (1, 2, 3)]
        print(f"{cat_id:<14} {len(events):>7} {elagues:>8} {geo:>7} {fr:>7} {t[0]:>5} {t[1]:>6} {t[2]:>7}")
        total += len(events)
        geo_total += geo
        manifest.append({"id": cat_id, "label": out["label"],
                         "file": f"data/{cat_id}.json", "count": len(events)})

    (DST / "manifest.json").write_text(
        json.dumps({"categories": manifest, "total": total},
                   ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nTotal : {total} événements ({geo_total} géolocalisés) "
          f"dans {len(manifest)} catégories.")
    print(f"Écrit dans {DST}")
    print("\nLancer l'application :  python -m http.server 8000 -d web")
    print("puis ouvrir            :  http://localhost:8000")


if __name__ == "__main__":
    main()
