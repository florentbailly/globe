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


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"Aucune extraction trouvée dans {SRC} — lancer extract_events.py d'abord.")
    DST.mkdir(parents=True, exist_ok=True)

    manifest = []
    print(f"{'Catégorie':<14} {'Évts':>7} {'Géo':>7} {'FR':>7} {'T1':>5} {'T2':>6} {'T3':>7}")
    total = geo_total = 0
    for f in sorted(SRC.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        events = sorted(data["events"], key=lambda e: (e["year"], -e["sl"]))
        cat_id = data["category"]
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
        print(f"{cat_id:<14} {len(events):>7} {geo:>7} {fr:>7} {t[0]:>5} {t[1]:>6} {t[2]:>7}")
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
