"""Shared paths, constants and helpers for the Joto Mjini pipeline."""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
INTERIM = DATA / "interim"
PROCESSED = DATA / "processed"
RASTERS = PROCESSED / "rasters"
SITE_DATA = ROOT / "site" / "public" / "data"
FIGURES = ROOT / "outputs" / "figures"
LOGS = ROOT / "logs"

for _p in (RAW, INTERIM, PROCESSED, RASTERS, SITE_DATA, FIGURES, LOGS):
    _p.mkdir(parents=True, exist_ok=True)

UTM = "EPSG:32737"   # UTM zone 37S, analysis projection
WGS84 = "EPSG:4326"
WEB = "EPSG:3857"
NAIROBI_TZ = ZoneInfo("Africa/Nairobi")
BUFFER_M = 2000      # study area buffer around the county
GRID_RES = 30        # metres, aligned to the Landsat grid

BOUNDARY = PROCESSED / "nairobi_boundary.geojson"
WARDS = PROCESSED / "nairobi_wards.geojson"
PLACES = PROCESSED / "nairobi_places.geojson"
GRID = INTERIM / "grid_30m.tif"


def now_local() -> str:
    return datetime.now(NAIROBI_TZ).strftime("%Y-%m-%d %H:%M")


def get_logger(name: str) -> logging.Logger:
    """Logger that writes timestamped lines to logs/<name>.log and stderr."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    fh = logging.FileHandler(LOGS / f"{name}.log")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def should_skip(path: Path, force: bool) -> bool:
    return path.exists() and not force
