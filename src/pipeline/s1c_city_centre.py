# Copyright (c) 2026 Stephane Ngugi. All rights reserved. See LICENSE.
"""City centre comparison area for F3: the downtown grid, traced from OpenStreetMap roads (DECISIONS D51).

The area people call "town": inside Uhuru Highway (west), University Way (north), Tom Mboya Street
(east, the River Road side) and Haile Selassie Avenue (south). Moi Avenue is used only north of MOI_CUT_LAT,
to close the short gap between the east end of University Way and the north end of Tom Mboya Street; further
south it runs inside the block and is left out, so the strip between Moi Avenue and Tom Mboya Street is included.

Method: buffer the road centrelines by GAP_M so dual carriageways and small gaps at junctions close, take the
enclosed holes of that buffered network, keep the one containing ANCHOR (Kenyatta Avenue at Kimathi Street)
and buffer it back out by GAP_M so the edge sits on the road centrelines.

Run: uv run python -m src.pipeline.s1c_city_centre
"""
from __future__ import annotations

import json

import geopandas as gpd
import requests
from shapely.geometry import LineString, Polygon, box
from shapely.ops import nearest_points, unary_union

from src.config import PROCESSED, ROOT, UTM, WGS84, get_logger
from src.pipeline.s1_boundaries import OVERPASS

log = get_logger("s1c_city_centre")

RAW = ROOT / "data" / "raw" / "osm_cbd" / "cbd_roads.json"
OUT = PROCESSED / "city_centre.geojson"
ROADS = ["Uhuru Highway", "University Way", "Moi Avenue", "Tom Mboya Street", "Haile Selassie Avenue"]
BBOX = (-1.300, 36.805, -1.270, 36.840)   # south, west, north, east
GAP_M = 30.0
MOI_CUT_LAT = -1.2822   # Moi Avenue north of here (just south of where Tom Mboya Street leaves it)
ANCHOR = (36.8219, -1.2841)   # Kenyatta Avenue at Kimathi Street


def fetch(force: bool = False) -> list[dict]:
    if RAW.exists() and not force:
        return json.loads(RAW.read_text())["elements"]
    names = "|".join(ROADS)
    q = (f'[out:json][timeout:120];way["highway"]["name"~"^({names})$"]'
         f"({BBOX[0]},{BBOX[1]},{BBOX[2]},{BBOX[3]});out geom;")
    r = requests.post(OVERPASS, data={"data": q}, timeout=180,
                      headers={"User-Agent": "joto-mjini-nairobi/1.0 (research)"})
    r.raise_for_status()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(r.text)
    log.info("OSM roads saved to %s (%d ways)", RAW, len(r.json()["elements"]))
    return r.json()["elements"]


def build(force: bool = False) -> gpd.GeoDataFrame:
    els = fetch(force)
    lines = gpd.GeoDataFrame(
        {"name": [e["tags"]["name"] for e in els], "osm_id": [f"way/{e['id']}" for e in els]},
        geometry=[LineString([(p["lon"], p["lat"]) for p in e["geometry"]]) for e in els], crs=WGS84).to_crs(UTM)
    cut, south = gpd.GeoSeries([box(36.0, MOI_CUT_LAT, 37.5, -1.0), box(36.0, -1.5, 37.5, MOI_CUT_LAT)],
                               crs=WGS84).to_crs(UTM)
    moi = lines["name"] == "Moi Avenue"
    lines.loc[moi, "geometry"] = lines.loc[moi].geometry.intersection(cut)
    lines = lines[~lines.geometry.is_empty]
    # Tom Mboya Street leaves Moi Avenue at the Moi Avenue junction; OSM has a short gap there, so join the
    # Moi Avenue stub to the start of Tom Mboya Street (the part south of the cut) with a straight line.
    tom = lines[lines["name"] == "Tom Mboya Street"].geometry.intersection(south).union_all()
    link = LineString(nearest_points(lines.loc[lines["name"] == "Moi Avenue"].geometry.union_all(), tom))
    net = unary_union(list(lines.buffer(GAP_M).geometry) + [link.buffer(GAP_M)])
    holes = [Polygon(r) for g in getattr(net, "geoms", [net]) for r in g.interiors]
    anchor = gpd.GeoSeries.from_xy([ANCHOR[0]], [ANCHOR[1]], crs=WGS84).to_crs(UTM).iloc[0]
    keep = [h for h in holes if h.contains(anchor)]
    if len(keep) != 1:
        raise RuntimeError(f"expected 1 enclosed face around the anchor, found {len(keep)}; check the road network")
    poly = keep[0].buffer(GAP_M)
    gdf = gpd.GeoDataFrame({"name": ["City centre (downtown grid)"],
                            "definition": ["inside Uhuru Highway, University Way, Tom Mboya Street and Haile "
                                           "Selassie Avenue, traced from OpenStreetMap road centrelines"],
                            "area_km2": [round(poly.area / 1e6, 3)]}, geometry=[poly], crs=UTM)
    gdf.to_crs(WGS84).to_file(OUT, driver="GeoJSON")
    ids = lines[lines.intersects(poly.buffer(GAP_M + 5))].sort_values(["name", "osm_id"])
    ids[["name", "osm_id"]].to_csv(ROOT / "analysis" / "tables" / "city_centre_osm_road_ids.csv", index=False)
    log.info("City centre polygon %.3f km2 -> %s", poly.area / 1e6, OUT)
    return gdf


if __name__ == "__main__":
    build(force="--force" in __import__("sys").argv)
