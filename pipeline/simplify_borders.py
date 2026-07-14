#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["shapely"]
# ///
"""Simplifie les geometries des frontieres historiques pour fluidifier le rendu.

Les frontieres du dataset ont une precision de l'ordre du siecle : conserver
des littoraux au metre pres est du gaspillage pur. Ce script applique :
  - reparation des geometries sources invalides (make_valid) ;
  - Douglas-Peucker (shapely, topologie preservee) avec une tolerance
    par defaut de 0.05 degre (~5 km) ;
  - quantification a 3 decimales (~110 m) via set_precision, qui preserve
    la validite topologique (un arrondi naif effondre certains anneaux et
    fait deborder la triangulation de globe.gl sur les oceans) ;
  - suppression des composantes non surfaciques et des anneaux degeneres.

Gain attendu : fichiers et cout de triangulation divises par 5 a 10.

Usage :
    uv run simplify_borders.py                 # tolerance 0.05
    uv run simplify_borders.py --tolerance 0.1

Le script travaille en place dans data/borders. Idempotent. Pour retrouver
les originaux : supprimer les fichiers et relancer fetch_borders.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import shapely
from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid

HERE = Path(__file__).resolve().parent
CANDIDATS = [HERE.parent / "data" / "borders", HERE.parent / "web" / "data" / "borders"]


def arrondir(coords, ndigits=3):
    if isinstance(coords, (int, float)):
        return round(coords, ndigits)
    return [arrondir(c, ndigits) for c in coords]


def compter_points(geom: dict) -> int:
    def rec(c):
        if isinstance(c[0], (int, float)):
            return 1
        return sum(rec(x) for x in c)
    return rec(geom["coordinates"]) if geom and geom.get("coordinates") else 0


def surfacique(geom):
    """Ne garde que les composantes Polygon/MultiPolygon d'une geometrie."""
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    if geom.geom_type == "GeometryCollection":
        polys = [g for g in geom.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        return unary_union(polys) if polys else None
    return None


def nettoyer(geom, tolerance: float):
    """make_valid -> simplify -> set_precision : geometrie valide sur grille 1e-3."""
    s = shape(geom)
    if not s.is_valid:
        s = make_valid(s)
    s = s.simplify(tolerance, preserve_topology=True)
    # quantification topologiquement sure (l'arrondi naif cree des anneaux
    # degeneres et des auto-intersections que earcut remplit n'importe comment)
    s = shapely.set_precision(s, 1e-3)
    if not s.is_valid:
        s = make_valid(s)
    s = surfacique(s)
    if s is None or s.is_empty:
        return None
    return s


def simplifier_fichier(path: Path, tolerance: float) -> tuple[int, int, int, int]:
    fc = json.loads(path.read_text(encoding="utf-8"))
    avant_pts = apres_pts = 0
    avant_octets = path.stat().st_size
    for feat in fc.get("features", []):
        geom = feat.get("geometry")
        if not geom:
            continue
        avant_pts += compter_points(geom)
        try:
            propre = nettoyer(geom, tolerance)
            if propre is not None:
                nouveau = mapping(propre)
                # les coordonnees sont deja sur la grille 1e-3 : l'arrondi est
                # exact et ne sert qu'a compacter le JSON (12.3450000001 -> 12.345)
                nouveau["coordinates"] = arrondir(nouveau["coordinates"])
                feat["geometry"] = nouveau
            else:
                feat["geometry"] = None   # geometrie vide apres nettoyage
        except Exception:
            pass   # geometrie recalcitrante : on garde l'originale
        if feat["geometry"]:
            apres_pts += compter_points(feat["geometry"])
    path.write_text(json.dumps(fc, separators=(",", ":")), encoding="utf-8")
    return avant_pts, apres_pts, avant_octets, path.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser(description="Simplification des frontieres")
    parser.add_argument("--tolerance", type=float, default=0.05,
                        help="tolerance Douglas-Peucker en degres (defaut 0.05 ~ 5 km)")
    args = parser.parse_args()

    dossier = next((d for d in CANDIDATS if d.exists()), None)
    if not dossier:
        raise SystemExit("Dossier borders introuvable (lancer fetch_borders.py d'abord).")

    fichiers = sorted(f for f in dossier.glob("*.json") if f.stem.lstrip("-").isdigit())
    print(f"{len(fichiers)} instantanes dans {dossier} (tolerance {args.tolerance} deg)\n")
    tp0 = tp1 = to0 = to1 = 0
    for f in fichiers:
        p0, p1, o0, o1 = simplifier_fichier(f, args.tolerance)
        tp0 += p0; tp1 += p1; to0 += o0; to1 += o1
        print(f"  {f.name:>12} : {p0:>7} -> {p1:>6} points | {o0//1024:>5} -> {o1//1024:>4} Ko")
    if tp0:
        print(f"\nTotal : {tp0} -> {tp1} points (-{100 - 100*tp1//tp0} %), "
              f"{to0//1024**2} -> {to1//1024**2} Mo (-{100 - 100*to1//to0} %)")


if __name__ == "__main__":
    main()
