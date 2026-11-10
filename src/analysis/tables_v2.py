"""v2 tables for the heatmap tables and the highlighted chart (chunk 4).

T1 builtup_by_subcounty.csv   built-up share of each of the 17 sub-counties (constituencies), GHSL epochs
T2 ward_cover_extremes.csv    land cover shares in the 10 hottest and 10 coolest wards by where people live
T3 daily_tmax_anomaly.csv     daily maximum air temperature since January 2023 minus the 1991 to 2020 normal
                              for that day of the year (ERA5 via Open-Meteo)
Summary numbers go to analysis/results_extra.json["tables_v2"] and FINDINGS.md (T1 to T3).

Run: uv run python -m src.analysis.tables_v2
"""
from __future__ import annotations

import json
import shutil

import geopandas as gpd
import numpy as np
import pandas as pd
from rasterio.features import rasterize

from src.analysis.layers import load
from src.config import PROCESSED, RASTERS, ROOT, SITE_DATA, UTM, WARDS
from src.rasterio_utils import read, read_grid

TABLES = ROOT / "analysis" / "tables"
EXTRA = ROOT / "analysis" / "results_extra.json"
EPOCHS = [1975, 1990, 2000, 2010, 2020, 2025]
EL_NINO_START = "2026-05-01"   # DECISIONS D16


def builtup_by_subcounty() -> pd.DataFrame:
    """Built-up surface (km²) inside each sub-county divided by its area, per GHSL epoch (90 m grid)."""
    wards = gpd.read_file(WARDS).to_crs(UTM)
    sc = wards.dissolve("subcounty").reset_index()
    rows = []
    import rasterio
    for yr in EPOCHS:
        with rasterio.open(RASTERS / f"ghsl_built_{yr}.tif") as s:
            a = s.read(1).astype("float32")
            t = s.transform
        cell_km2 = abs(t.a * t.e) / 1e6
        for _, r in sc.iterrows():
            m = rasterize([(r.geometry, 1)], out_shape=a.shape, transform=t, fill=0) == 1
            built = float(np.nansum(a[m])) * cell_km2
            rows.append(dict(subcounty=r.subcounty, epoch=yr, built_pct=round(100 * built / (r.geometry.area / 1e6), 1),
                             area_km2=round(r.geometry.area / 1e6, 1)))
    df = pd.DataFrame(rows)
    order = df[df.epoch == 2020].sort_values("built_pct", ascending=False).subcounty.tolist()
    df["order"] = df["subcounty"].map({n: i for i, n in enumerate(order)})
    return df.sort_values(["order", "epoch"]).drop(columns="order")


def ward_cover_extremes() -> pd.DataFrame:
    L = load()
    grass, bare = read(RASTERS / "grass_fraction_30m.tif"), read(RASTERS / "bare_fraction_30m.tif")
    ws = pd.read_csv(TABLES / "ward_stats.csv")
    med = json.loads((ROOT / "analysis" / "results.json").read_text())["q1"]["county_median_c"]
    extra = []
    for i, w in L.wards.iterrows():
        m = L.ward_idx == i + 1
        extra.append(dict(ward_id=w.ward_id, grass_pct=100 * float(np.nanmean(grass[m])), bare_pct=100 * float(np.nanmean(bare[m]))))
    ws = ws.merge(pd.DataFrame(extra), on="ward_id")
    ws = ws.dropna(subset=["pop_weighted_lst_c"]).sort_values("pop_weighted_lst_c", ascending=False)
    hot, cool = ws.head(10).assign(group="hottest"), ws.tail(10).assign(group="coolest")
    out = pd.concat([hot, cool])
    out["diff_c"] = out["pop_weighted_lst_c"] - med
    cols = ["group", "ward_name", "tree_pct", "grass_pct", "built_pct", "bare_pct", "diff_c", "pop_weighted_lst_c"]
    return out[cols].round(1)


def daily_anomaly() -> tuple[pd.DataFrame, dict]:
    a = pd.read_csv(PROCESSED / "nairobi_daily_air_temp.csv", parse_dates=["date"])
    base = a[(a.date >= "1991-01-01") & (a.date <= "2020-12-31")].copy()
    base["doy"] = base.date.dt.day_of_year.clip(upper=365)
    # Normal for each day of the year: 1991 to 2020 mean, smoothed with a 31-day circular window.
    raw = base.groupby("doy")["temperature_2m_max"].mean().reindex(range(1, 366))
    ext = pd.concat([raw.iloc[-15:], raw, raw.iloc[:15]])
    normal = ext.rolling(31, center=True).mean().iloc[15:-15]
    normal.index = range(1, 366)
    d = a[a.date >= "2023-01-01"].copy()
    d["doy"] = d.date.dt.day_of_year.clip(upper=365)
    d["normal_c"] = d["doy"].map(normal).round(2)
    d["tmax_c"] = d["temperature_2m_max"]
    d["anomaly_c"] = (d["tmax_c"] - d["normal_c"]).round(1)
    d["el_nino"] = d.date >= EL_NINO_START
    rec = d.loc[d.tmax_c.idxmax()]
    en = d[d.el_nino]
    summ = dict(first=str(d.date.min().date()), last=str(d.date.max().date()),
                record_day=str(rec.date.date()), record_tmax_c=float(rec.tmax_c),
                el_nino_mean_anomaly_c=round(float(en.anomaly_c.mean()), 1),
                el_nino_share_days_above_normal_pct=round(100 * float((en.anomaly_c > 0).mean()), 1),
                before_mean_anomaly_c=round(float(d[~d.el_nino].anomaly_c.mean()), 1),
                normal_method="1991 to 2020 mean for each day of the year, smoothed with a 31-day circular window")
    out = d[["date", "tmax_c", "normal_c", "anomaly_c", "el_nino"]].copy()
    out["date"] = out.date.dt.strftime("%Y-%m-%d")
    return out, summ


def main() -> None:
    t1 = builtup_by_subcounty()
    t2 = ward_cover_extremes()
    t3, s3 = daily_anomaly()
    for df, name in ((t1, "builtup_by_subcounty.csv"), (t2, "ward_cover_extremes.csv"), (t3, "daily_tmax_anomaly.csv")):
        df.to_csv(TABLES / name, index=False)
        shutil.copy(TABLES / name, SITE_DATA / name)
    p20 = t1[t1.epoch.isin([1975, 2020])].pivot(index="subcounty", columns="epoch", values="built_pct")
    ex = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}
    ex["tables_v2"] = dict(
        builtup_by_subcounty=dict(most_built_2020=p20[2020].idxmax(), most_built_2020_pct=float(p20[2020].max()),
                                  least_built_2020=p20[2020].idxmin(), least_built_2020_pct=float(p20[2020].min()),
                                  largest_rise_1975_2020=(p20[2020] - p20[1975]).idxmax(),
                                  largest_rise_1975_2020_points=round(float((p20[2020] - p20[1975]).max()), 1)),
        ward_cover_extremes=dict(hottest_mean_tree_pct=round(float(t2[t2.group == "hottest"].tree_pct.mean()), 1),
                                 coolest_mean_tree_pct=round(float(t2[t2.group == "coolest"].tree_pct.mean()), 1),
                                 hottest_mean_built_pct=round(float(t2[t2.group == "hottest"].built_pct.mean()), 1),
                                 coolest_mean_built_pct=round(float(t2[t2.group == "coolest"].built_pct.mean()), 1)),
        daily_tmax=s3)
    EXTRA.write_text(json.dumps(ex, indent=2))
    print(json.dumps(ex["tables_v2"], indent=1))


if __name__ == "__main__":
    main()
