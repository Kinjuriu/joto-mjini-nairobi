"""Small raster helpers shared by pipeline and analysis."""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.transform import Affine

from src.config import BOUNDARY, GRID, UTM


def write_cog(path: Path, arr: np.ndarray, transform: Affine, crs: str = UTM,
              nodata: float | int | None = np.nan, dtype: str | None = None) -> Path:
    """Write a single-band or multi-band array as a Cloud Optimized GeoTIFF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    a = arr if arr.ndim == 3 else arr[None, ...]
    dtype = dtype or str(a.dtype)
    profile = dict(driver="COG", width=a.shape[2], height=a.shape[1], count=a.shape[0],
                   dtype=dtype, crs=crs, transform=transform, nodata=nodata,
                   compress="DEFLATE", predictor=3 if dtype.startswith("float") else 2,
                   blocksize=512, overview_resampling="average")
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(a.astype(dtype))
    return path


def read_grid() -> tuple[Affine, int, int]:
    with rasterio.open(GRID) as src:
        return src.transform, src.width, src.height


def read(path: Path) -> np.ndarray:
    with rasterio.open(path) as src:
        a = src.read(1).astype("float32")
        if src.nodata is not None and not np.isnan(src.nodata):
            a[a == src.nodata] = np.nan
        return a


def county_mask() -> np.ndarray:
    """Boolean mask of grid cells whose centre lies inside Nairobi County."""
    transform, w, h = read_grid()
    county = gpd.read_file(BOUNDARY).to_crs(UTM)
    return rasterize(county.geometry, out_shape=(h, w), transform=transform, fill=0,
                     default_value=1, dtype="uint8").astype(bool)


def polygon_mask(geoms, all_touched: bool = False) -> np.ndarray:
    transform, w, h = read_grid()
    return rasterize(geoms, out_shape=(h, w), transform=transform, fill=0, default_value=1,
                     dtype="uint8", all_touched=all_touched).astype(bool)
