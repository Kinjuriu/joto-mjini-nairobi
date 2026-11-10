"""Step 1: Nairobi County boundary, wards and place names.

Run: uv run python -m src.pipeline.s1_boundaries [--force]
"""
from __future__ import annotations

import argparse
import json

import geopandas as gpd
import pandas as pd
import requests

from src.config import BOUNDARY, CITY, CITY_NAME, PLACES, RAW, UTM, WARDS, WGS84, get_logger, should_skip

log = get_logger("s1_boundaries")

GB_API = "https://www.geoboundaries.org/api/current/gbOpen/KEN/{level}/"
OVERPASS = "https://overpass-api.de/api/interpreter"


def _gb_download(level: str) -> gpd.GeoDataFrame:
    meta = requests.get(GB_API.format(level=level), timeout=60).json()
    out = RAW / f"geoboundaries_KEN_{level}.geojson"
    if not out.exists():
        r = requests.get(meta["gjDownloadURL"], timeout=300)
        r.raise_for_status()
        out.write_bytes(r.content)
    (RAW / f"geoboundaries_KEN_{level}_meta.json").write_text(json.dumps(meta, indent=2))
    log.info("geoBoundaries %s: %s, licence %s", level, meta["boundarySource"], meta["boundaryLicense"])
    return gpd.read_file(out)


def boundary(force: bool = False) -> gpd.GeoDataFrame:
    if should_skip(BOUNDARY, force):
        return gpd.read_file(BOUNDARY)
    adm1 = _gb_download("ADM1")
    nbo = adm1[adm1["shapeName"].str.contains(CITY_NAME, case=False)].copy()
    if len(nbo) != 1:
        raise RuntimeError(f"Expected one {CITY_NAME} feature, got {len(nbo)}")
    nbo = nbo[["shapeName", "shapeID", "geometry"]].rename(columns={"shapeName": "name"}).to_crs(WGS84)
    nbo.to_file(BOUNDARY, driver="GeoJSON")
    area = nbo.to_crs(UTM).area.iloc[0] / 1e6
    log.info("%s boundary saved, area %.1f km2", CITY_NAME, area)
    return nbo


def wards(county: gpd.GeoDataFrame, force: bool = False) -> gpd.GeoDataFrame:
    if should_skip(WARDS, force):
        return gpd.read_file(WARDS)
    adm3 = _gb_download("ADM3").to_crs(UTM)
    c = county.to_crs(UTM)
    # Keep wards whose representative point falls inside the county.
    pts = adm3.copy()
    pts["geometry"] = adm3.representative_point()
    inside = gpd.sjoin(pts, c[["geometry"]], predicate="within").index
    w = adm3.loc[inside].copy()
    log.info("Wards inside %s County: %d", CITY_NAME, len(w))
    # Clip to the county outline so ward edges match the boundary exactly.
    w = gpd.clip(w, c)
    w = w[w.area > 1000]
    w["ward_name"] = w["shapeName"].str.strip().str.title().map(_fix_case)
    w = w.sort_values("ward_name").reset_index(drop=True)
    prefix = "NBO" if CITY == "nairobi" else CITY[:3].upper()
    w["ward_id"] = [f"{prefix}-{i + 1:03d}" for i in range(len(w))]
    w["area_km2"] = (w.area / 1e6).round(3)
    w = w[["ward_id", "ward_name", "shapeID", "area_km2", "geometry"]].to_crs(WGS84)
    w.to_file(WARDS, driver="GeoJSON")
    log.info("Saved %d wards, total area %.1f km2", len(w), w["area_km2"].sum())
    return w


def _fix_case(name: str) -> str:
    """Restore roman numerals after title-casing, e.g. 'Dandora Area Ii' -> 'Dandora Area II'."""
    import re
    return re.sub(r"\b(iv|vi{0,3}|i{1,3})\b", lambda m: m.group(0).upper(), name, flags=re.I)


def places(county: gpd.GeoDataFrame, force: bool = False) -> gpd.GeoDataFrame:
    if should_skip(PLACES, force):
        return gpd.read_file(PLACES)
    minx, miny, maxx, maxy = county.to_crs(WGS84).total_bounds
    bbox = f"{miny - 0.02},{minx - 0.02},{maxy + 0.02},{maxx + 0.02}"
    q = f"""
    [out:json][timeout:180];
    (
      node["place"~"^(suburb|neighbourhood|quarter)$"]({bbox});
      nwr["leisure"="park"]["name"]({bbox});
      nwr["landuse"="forest"]["name"]({bbox});
      nwr["boundary"="protected_area"]["name"]({bbox});
      nwr["leisure"="nature_reserve"]["name"]({bbox});
      nwr["landuse"="industrial"]["name"]({bbox});
      nwr["natural"="water"]["name"]({bbox});
    );
    out geom;
    """
    raw = RAW / "osm_places.json"
    if not raw.exists() or force:
        r = requests.post(OVERPASS, data={"data": q}, timeout=300,
                          headers={"User-Agent": "joto-mjini/0.1 (research)"})
        r.raise_for_status()
        raw.write_text(r.text)
    data = json.loads(raw.read_text())
    gdf = osm_json_to_gdf(data["elements"])
    gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty]
    c = county.to_crs(WGS84)
    gdf = gdf[gdf.intersects(c.union_all().buffer(0.02))]
    gdf.to_file(PLACES, driver="GeoJSON")
    log.info("Saved %d place features", len(gdf))
    return gdf


def osm_json_to_gdf(elements: list[dict]) -> gpd.GeoDataFrame:
    """Turn Overpass `out geom` elements into points (nodes) and polygons (ways, relations)."""
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import polygonize, unary_union

    rows = []
    for e in elements:
        tags = e.get("tags", {})
        name = tags.get("name")
        if not name:
            continue
        kind = (tags.get("place") or tags.get("leisure") or tags.get("landuse")
                or tags.get("boundary") or tags.get("natural"))
        geom = None
        if e["type"] == "node":
            geom = Point(e["lon"], e["lat"])
        elif e["type"] == "way" and "geometry" in e:
            coords = [(p["lon"], p["lat"]) for p in e["geometry"]]
            if len(coords) >= 4 and coords[0] == coords[-1]:
                geom = Polygon(coords)
            elif len(coords) >= 2:
                geom = LineString(coords)
        elif e["type"] == "relation":
            lines = []
            for m in e.get("members", []):
                if m.get("type") == "way" and "geometry" in m and m.get("role") in ("outer", ""):
                    lines.append(LineString([(p["lon"], p["lat"]) for p in m["geometry"]]))
            if lines:
                polys = list(polygonize(unary_union(lines)))
                if polys:
                    geom = unary_union(polys)
        if geom is None or geom.geom_type == "LineString":
            continue
        rows.append({"osm_id": f"{e['type']}/{e['id']}", "name": name,
                     "name_sw": tags.get("name:sw"), "kind": kind, "geometry": geom})
    return gpd.GeoDataFrame(pd.DataFrame(rows), geometry="geometry", crs=WGS84)


def main(force: bool = False) -> None:
    c = boundary(force)
    wards(c, force)
    places(c, force)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    main(ap.parse_args().force)
