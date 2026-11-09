"""Steps 4 and 5: daily air temperature for Nairobi (Open-Meteo, ERA5) and the RONI El Nino index.

Run: uv run python -m src.pipeline.s4_climate [--force]
"""
from __future__ import annotations

import argparse
import io
from datetime import date, timedelta

import pandas as pd
import requests

from src.config import PROCESSED, RAW, get_logger, should_skip

log = get_logger("s4_climate")

OPEN_METEO = "https://archive-api.open-meteo.com/v1/archive"
CBD = (-1.286, 36.817)
RONI_URL = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/roni/"
SEASONS = ["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]


def air_temperature(force: bool = False) -> pd.DataFrame:
    out = PROCESSED / "nairobi_daily_air_temp.csv"
    if should_skip(out, force):
        return pd.read_csv(out, parse_dates=["date"])
    end = (date.today() - timedelta(days=1)).isoformat()
    params = dict(latitude=CBD[0], longitude=CBD[1], start_date="1991-01-01", end_date=end,
                  daily="temperature_2m_max,temperature_2m_min,temperature_2m_mean",
                  timezone="Africa/Nairobi")
    r = requests.get(OPEN_METEO, params=params, timeout=300)
    r.raise_for_status()
    j = r.json()
    (RAW / "open_meteo_response_meta.txt").write_text(
        f"request={r.url}\nlatitude={j['latitude']} longitude={j['longitude']} elevation={j['elevation']}\n")
    df = pd.DataFrame(j["daily"]).rename(columns={"time": "date"})
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["temperature_2m_max"])
    df.to_csv(out, index=False)
    log.info("Open-Meteo: %d days %s to %s, grid cell %.4f, %.4f, elevation %s m", len(df),
             df["date"].min().date(), df["date"].max().date(), j["latitude"], j["longitude"], j["elevation"])
    return df


def roni(force: bool = False) -> pd.DataFrame:
    out = PROCESSED / "roni.csv"
    if should_skip(out, force):
        return pd.read_csv(out)
    html = requests.get(RONI_URL, timeout=120).text
    (RAW / "roni_page.html").write_text(html)
    tables = pd.read_html(io.StringIO(html))
    rows = []
    for t in tables:
        t = t.copy()
        t.columns = [str(c).strip() for c in t.iloc[0]] if "Year" not in [str(c) for c in t.columns] else t.columns
        for _, r in t.iterrows():
            yr = str(r.iloc[0]).strip()
            if not yr.isdigit():
                continue
            for i, s in enumerate(SEASONS):
                try:
                    v = float(r.iloc[i + 1])
                except (ValueError, IndexError):
                    continue
                rows.append({"year": int(yr), "season": s, "centre_month": i + 1, "roni": v})
    df = pd.DataFrame(rows).drop_duplicates(["year", "season"]).sort_values(["year", "centre_month"])
    df.to_csv(out, index=False)
    log.info("RONI: %d values, %s to %s; latest %s", len(df), df["year"].min(), df["year"].max(),
             df.tail(3)[["year", "season", "roni"]].to_dict("records"))
    return df


def main(force: bool = False) -> None:
    for fn in (air_temperature, roni):
        try:
            fn(force)
        except Exception as e:
            log.error("%s failed: %s", fn.__name__, e)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    main(ap.parse_args().force)
