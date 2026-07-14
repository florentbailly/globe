#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///
"""Phase 2 - Telecharge les frontieres historiques mondiales.

Source : depot aourednik/historical-basemaps (licence libre, precision
assumee ~siecle pour les epoques anciennes, ~decennie ensuite).

Copie chaque instantane world_*.geojson vers data/borders/{annee}.json
(annees negatives = av. J.-C.) et ecrit l'index des annees disponibles.

Usage :  uv run fetch_borders.py
Volume : ~49 fichiers, ~65 Mo au total.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

RAW = "https://raw.githubusercontent.com/aourednik/historical-basemaps/master/geojson"
DST = Path(__file__).resolve().parent.parent / "data" / "borders"
ANNEE_MIN = -4000   # un instantane avant -3000 sert de base au demarrage

# Instantanes disponibles dans le depot (verifie le 2026-07-11).
# Pour rafraichir cette liste : voir le dossier geojson/ du depot GitHub.
INSTANTANES_BC = [4000, 3000, 2000, 1500, 1000, 700, 500, 400, 323, 300, 200, 100, 1]
INSTANTANES_AD = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1100, 1200,
                  1279, 1300, 1400, 1492, 1500, 1530, 1600, 1650, 1700, 1715,
                  1783, 1800, 1815, 1880, 1900, 1914, 1920, 1930, 1938, 1945,
                  1960, 1994, 2000, 2010]


def fichiers() -> list[tuple[int, str]]:
    paires = [(-a, f"world_bc{a}.geojson") for a in INSTANTANES_BC]
    paires += [(a, f"world_{a}.geojson") for a in INSTANTANES_AD]
    return sorted((a, f) for a, f in paires if a >= ANNEE_MIN)


def main() -> None:
    limite = int(sys.argv[sys.argv.index("--limite") + 1]) if "--limite" in sys.argv else None
    DST.mkdir(parents=True, exist_ok=True)
    annees, echecs = [], []
    liste = fichiers()[:limite]
    for i, (annee, nom) in enumerate(liste, 1):
        cible = DST / f"{annee}.json"
        if cible.exists():
            print(f"[{i}/{len(liste)}] {annee} deja present")
            annees.append(annee)
            continue
        print(f"[{i}/{len(liste)}] {nom} -> {cible.name} ...", end=" ", flush=True)
        try:
            r = requests.get(f"{RAW}/{nom}", timeout=120,
                             headers={"User-Agent": "HistoireGlobe/0.3"})
            r.raise_for_status()
            data = r.json()          # validation JSON avant ecriture
            n = len(data.get("features", []))
            cible.write_bytes(r.content)
            annees.append(annee)
            print(f"{n} entites, {len(r.content)//1024} Ko")
        except Exception as exc:
            echecs.append(nom)
            print(f"ECHEC ({exc})")
    (DST / "index.json").write_text(json.dumps({"years": sorted(annees)}), encoding="utf-8")
    print(f"\n{len(annees)} instantanes installes dans {DST}")
    if echecs:
        print(f"Echecs a relancer : {', '.join(echecs)}")


if __name__ == "__main__":
    main()
