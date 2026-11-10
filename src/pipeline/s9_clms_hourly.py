"""Step 9 (v2): hourly land surface temperature for one hot day, from the Copernicus Land Monitoring Service.

Product: CLMS Global Land Surface Temperature, hourly, ~3 km, version 3 (Meteosat over Africa), served by
the Copernicus Data Space Ecosystem through the Sentinel Hub Process API (collection
byoc-12225aec-26dd-4e2c-bbfd-994c253c1ba8). LST in kelvin = raw / 100 + 273.15, so °C = raw / 100.

The day: the hottest clear Landsat morning of the 2026 hot season (highest county median in the scene
catalogue), so the same morning's Landsat scene can sharpen the hourly maps (src/animations/day_of_heat.py).

Credentials come from .env (CDSE_CLIENT_ID, CDSE_CLIENT_SECRET) through code and are never printed.
Outputs: data/raw/clms_lst/<date>/lst_<HHMM>utc.tif (°C, QFLAG, ERRORBAR) and meta.json.

Run: uv run python -m src.pipeline.s9_clms_hourly
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

from src.config import PROCESSED, RAW, ROOT, get_logger

log = get_logger("s9_clms_hourly")

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
PROCESS_URL = "https://sh.dataspace.copernicus.eu/api/v1/process"
COLLECTION = "byoc-12225aec-26dd-4e2c-bbfd-994c253c1ba8"
BBOX = [36.50, -1.60, 37.25, -1.00]      # lon/lat box around the county with a margin
RES = 0.03                               # degrees, about 3.3 km: the product's native grid spacing
HOURS_UTC = list(range(3, 17))           # 06:00 to 19:00 Nairobi time
EVALSCRIPT = """//VERSION=3
function setup() {
  return { input: ["LST", "QFLAG", "ERRORBAR", "dataMask"], output: { bands: 3, sampleType: "FLOAT32" },
           mosaicking: "SIMPLE" };
}
function evaluatePixel(s) {
  if (s.dataMask === 0) { return [NaN, NaN, NaN]; }
  return [s.LST / 100, s.QFLAG, s.ERRORBAR / 100];
}
"""


def hottest_2026_day() -> str:
    cat = pd.read_csv(PROCESSED / "landsat_scene_catalogue.csv")
    cat = cat[cat["usable"] & cat["date"].str.startswith("2026-0") & cat["date"].str[5:7].isin(["01", "02", "03"])]
    return cat.sort_values("lst_median_c", ascending=False).iloc[0]["date"]


def token() -> str:
    load_dotenv(ROOT / ".env")
    cid, sec = os.environ.get("CDSE_CLIENT_ID"), os.environ.get("CDSE_CLIENT_SECRET")
    if not cid or not sec:
        raise RuntimeError("CDSE credentials missing")
    r = requests.post(TOKEN_URL, data={"grant_type": "client_credentials", "client_id": cid, "client_secret": sec},
                      timeout=60)
    r.raise_for_status()
    return r.json()["access_token"]


def fetch(day: str) -> dict:
    out = RAW / "clms_lst" / day
    out.mkdir(parents=True, exist_ok=True)
    tok = token()
    w = int(round((BBOX[2] - BBOX[0]) / RES))
    h = int(round((BBOX[3] - BBOX[1]) / RES))
    got = []
    for hr in HOURS_UTC:
        f = out / f"lst_{hr:02d}00utc.tif"
        if f.exists():
            got.append(hr)
            continue
        t0 = pd.Timestamp(f"{day}T{hr:02d}:00:00Z") - pd.Timedelta(minutes=30)
        t1 = t0 + pd.Timedelta(minutes=59, seconds=59)
        body = {
            "input": {"bounds": {"bbox": BBOX, "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
                      "data": [{"type": COLLECTION, "dataFilter": {"timeRange": {
                          "from": t0.strftime("%Y-%m-%dT%H:%M:%SZ"), "to": t1.strftime("%Y-%m-%dT%H:%M:%SZ")}}}]},
            "output": {"width": w, "height": h, "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}]},
            "evalscript": EVALSCRIPT,
        }
        r = requests.post(PROCESS_URL, json=body, headers={"Authorization": f"Bearer {tok}"}, timeout=120)
        if r.status_code != 200:
            log.warning("hour %02d UTC: HTTP %s %s", hr, r.status_code, r.text[:200])
            continue
        f.write_bytes(r.content)
        got.append(hr)
        log.info("hour %02d UTC saved", hr)
    meta = dict(date=day, hours_utc=got, bbox=BBOX, res_deg=RES, collection=COLLECTION,
                product="CLMS Global Land Surface Temperature, hourly, ~3 km, v3")
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def summary(day: str) -> None:
    import rasterio
    for f in sorted((RAW / "clms_lst" / day).glob("lst_*utc.tif")):
        with rasterio.open(f) as s:
            a = s.read(1)
        v = a[np.isfinite(a)]
        log.info("%s: %d of %d pixels valid, median %.1f °C", f.name, v.size, a.size, np.median(v) if v.size else np.nan)


if __name__ == "__main__":
    d = hottest_2026_day()
    log.info("Hottest clear Landsat morning of the 2026 hot season: %s", d)
    fetch(d)
    summary(d)
