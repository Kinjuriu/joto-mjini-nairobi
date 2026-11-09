"""Load the analysis layers on the shared 30 m grid, plus ward and place geometries."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import geopandas as gpd
import numpy as np
from rasterio.features import rasterize

from src.config import PLACES, RASTERS, UTM, WARDS
from src.rasterio_utils import county_mask, read, read_grid

# Fixed surface temperature breaks (deg C) used on every surface temperature map and figure.
LST_BREAKS = [24, 28, 32, 35, 38, 41, 44, 48]


@dataclass
class Layers:
    hot: np.ndarray
    cool: np.ndarray
    ndvi: np.ndarray
    tree: np.ndarray
    built: np.ndarray
    wc: np.ndarray
    pop: np.ndarray
    county: np.ndarray
    ward_idx: np.ndarray   # 0 = outside any ward, else 1-based index into `wards`
    wards: gpd.GeoDataFrame


@lru_cache(maxsize=1)
def load() -> Layers:
    t, w, h = read_grid()
    wards = gpd.read_file(WARDS).to_crs(UTM).reset_index(drop=True)
    ward_idx = rasterize(((g, i + 1) for i, g in enumerate(wards.geometry)), out_shape=(h, w),
                         transform=t, fill=0, dtype="int32")
    return Layers(
        hot=read(RASTERS / "lst_hot_season_median.tif"),
        cool=read(RASTERS / "lst_cool_season_median.tif"),
        ndvi=read(RASTERS / "ndvi_hot_season_median.tif"),
        tree=read(RASTERS / "tree_fraction_30m.tif"),
        built=read(RASTERS / "built_fraction_30m.tif"),
        wc=read(RASTERS / "worldcover_majority_30m.tif"),
        pop=np.nan_to_num(read(RASTERS / "population_30m.tif"), nan=0.0),
        county=county_mask(),
        ward_idx=ward_idx,
        wards=wards,
    )


def places() -> gpd.GeoDataFrame:
    p = gpd.read_file(PLACES).to_crs(UTM)
    return p


def place_polygon(name: str, kind: str | None = None) -> gpd.GeoDataFrame:
    """Largest OSM polygon with exactly this name (and kind, if given)."""
    p = places()
    sel = p[(p["name"] == name) & p.geom_type.isin(["Polygon", "MultiPolygon"])]
    if kind:
        sel = sel[sel["kind"] == kind]
    if sel.empty:
        raise KeyError(name)
    return sel.loc[[sel.area.idxmax()]]
