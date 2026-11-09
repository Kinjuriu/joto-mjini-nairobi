"""Step 2b: seasonal surface temperature and NDVI composites from usable Landsat scenes.

Run: uv run python -m src.pipeline.s2b_composites [--force]
"""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from src.config import PROCESSED, RASTERS, get_logger, should_skip
from src.pipeline.s2_landsat import CATALOGUE, SCENES
from src.rasterio_utils import read, read_grid, write_cog

log = get_logger("s2b_composites")

HOT_MONTHS = (1, 2, 3)
COOL_MONTHS = (6, 7, 8)
FIRST_YEAR = 2023
MIN_SCENES = 4
BY_YEAR_DIR = RASTERS / "lst_hot_season_by_year"
META = PROCESSED / "composites_meta.json"


def usable_catalogue() -> pd.DataFrame:
    c = pd.read_csv(CATALOGUE)
    c["date"] = pd.to_datetime(c["date"])
    c["year"], c["month"] = c["date"].dt.year, c["date"].dt.month
    u = c[c["usable"]].copy()
    u = u[[(SCENES / f"{s}_lst_c.tif").exists() for s in u["scene_id"]]]
    return u


def select_season(u: pd.DataFrame, months: tuple[int, ...]) -> tuple[pd.DataFrame, int]:
    """Scenes in `months` from FIRST_YEAR on; extend back a year at a time until MIN_SCENES."""
    s = u[u["month"].isin(months)]
    start = FIRST_YEAR
    while (s["year"] >= start).sum() < MIN_SCENES and start > s["year"].min():
        start -= 1
    return s[s["year"] >= start], start


def median_stack(ids: list[str], kind: str = "lst_c") -> tuple[np.ndarray, np.ndarray]:
    stack = np.stack([read(SCENES / f"{i}_{kind}.tif") for i in ids])
    with np.errstate(all="ignore"):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            med = np.nanmedian(stack, axis=0)
    count = np.isfinite(stack).sum(axis=0).astype("uint8")
    return med.astype("float32"), count


def main(force: bool = False) -> dict:
    t, _, _ = read_grid()
    u = usable_catalogue()
    meta: dict = {}

    for name, months in [("hot_season", HOT_MONTHS), ("cool_season", COOL_MONTHS)]:
        s, start = select_season(u, months)
        out = RASTERS / f"lst_{name}_median.tif"
        ids = s["scene_id"].tolist()
        meta[name] = dict(months=list(months), first_year=start, n_scenes=len(ids),
                          scenes=ids, dates=s["date"].dt.strftime("%Y-%m-%d").tolist())
        log.info("%s: %d scenes from %d onward", name, len(ids), start)
        if not should_skip(out, force):
            med, cnt = median_stack(ids)
            write_cog(out, med, t)
            write_cog(RASTERS / f"lst_{name}_count.tif", cnt, t, nodata=None, dtype="uint8")
        if name == "hot_season":
            nd = RASTERS / "ndvi_hot_season_median.tif"
            if not should_skip(nd, force):
                med, _ = median_stack(ids, "ndvi")
                write_cog(nd, med, t)

    # Hottest clear day: usable scene with the highest county median.
    hot = u.sort_values("lst_median_c", ascending=False).iloc[0]
    out = RASTERS / "lst_hottest_clear_day.tif"
    if not should_skip(out, force):
        write_cog(out, read(SCENES / f"{hot['scene_id']}_lst_c.tif"), t)
    meta["hottest_clear_day"] = dict(scene_id=hot["scene_id"], date=hot["date"].strftime("%Y-%m-%d"),
                                     county_median_c=float(hot["lst_median_c"]))
    log.info("Hottest clear day: %s, county median %.1f C", hot["date"].date(), hot["lst_median_c"])

    # Jan to Mar composite per year, years 2014 onward with at least 2 usable scenes.
    BY_YEAR_DIR.mkdir(parents=True, exist_ok=True)
    meta["by_year"] = {}
    hs = u[u["month"].isin(HOT_MONTHS) & (u["year"] >= 2014)]
    for y, g in hs.groupby("year"):
        if len(g) < 2:
            continue
        out = BY_YEAR_DIR / f"{y}.tif"
        if not should_skip(out, force):
            med, _ = median_stack(g["scene_id"].tolist())
            write_cog(out, med, t)
        meta["by_year"][int(y)] = dict(n_scenes=len(g), dates=g["date"].dt.strftime("%Y-%m-%d").tolist())
    log.info("By-year composites: %s", {k: v["n_scenes"] for k, v in meta["by_year"].items()})

    # Scenes since the start of the 2026 El Nino period (May 2026), listed only.
    c = pd.read_csv(CATALOGUE)
    en = c[(pd.to_datetime(c["date"]) >= "2026-05-01") & c["usable"]]
    en.to_csv(PROCESSED / "lst_2026_el_nino_period.csv", index=False)
    meta["el_nino_2026_usable_scenes"] = len(en)
    META.write_text(json.dumps(meta, indent=2))
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    main(ap.parse_args().force)
