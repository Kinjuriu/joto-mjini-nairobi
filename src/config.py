"""Shared paths, constants and helpers for the Joto Mjini Nairobi pipeline."""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import os

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# City switch. Nairobi is the default and keeps the original paths; other cities (optional, for
# comparison) write to their own subfolders. Run e.g. `JOTO_CITY=kisumu uv run python -m ...`.
CITIES = {
    "nairobi": dict(name="Nairobi", utm="EPSG:32737"),
    "kisumu": dict(name="Kisumu", utm="EPSG:32736"),
}
CITY = os.environ.get("JOTO_CITY", "nairobi").lower()
CITY_NAME = CITIES[CITY]["name"]
_SUB = "" if CITY == "nairobi" else CITY
RAW = DATA / "raw" / _SUB
INTERIM = DATA / "interim" / _SUB
PROCESSED = DATA / "processed" / _SUB
RASTERS = PROCESSED / "rasters"
SITE_DATA = ROOT / "site" / "public" / "data"
FIGURES = ROOT / "outputs" / "figures"
LOGS = ROOT / "logs"

for _p in (RAW, INTERIM, PROCESSED, RASTERS, SITE_DATA, FIGURES, LOGS):
    _p.mkdir(parents=True, exist_ok=True)

UTM = CITIES[CITY]["utm"]   # analysis projection: UTM 37S for Nairobi, 36S for Kisumu
WGS84 = "EPSG:4326"
WEB = "EPSG:3857"
NAIROBI_TZ = ZoneInfo("Africa/Nairobi")
BUFFER_M = 2000      # study area buffer around the county
GRID_RES = 30        # metres, aligned to the Landsat grid

BOUNDARY = PROCESSED / f"{CITY}_boundary.geojson"
WARDS = PROCESSED / f"{CITY}_wards.geojson"
PLACES = PROCESSED / f"{CITY}_places.geojson"
GRID = INTERIM / "grid_30m.tif"


def now_local() -> str:
    return datetime.now(NAIROBI_TZ).strftime("%Y-%m-%d %H:%M")


def get_logger(name: str) -> logging.Logger:
    """Logger that writes timestamped lines to logs/<name>.log and stderr."""
    if CITY != "nairobi":
        name = f"{CITY}_{name}"
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
