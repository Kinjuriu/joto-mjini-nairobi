"""Numbers for the v3 story text (16 November 2026).

Writes analysis/results_extra.json["copy_v3"] so the page reads every number through {{x.copy_v3...}}:

1. forests: hot-season median surface temperature inside each of the three forests outlined on the map
   (site/public/data/forests.geojson), cells whose centres fall inside the outline, the same rule as
   core.q5_park_rings. Karura and the Arboretum are checked against results.json q5.
2. day_of_heat: the hourly chart's numbers (site/public/data/day_of_heat_hourly.csv), so the chart title
   and caption no longer type "26 °C" and "hotter at noon" by hand.
3. growth: where built-up land was added between 1990 and 2020, by sub-county
   (analysis/tables/builtup_by_subcounty.csv, from tables_v2.py).

Needs only numpy, pandas, geopandas and rasterio:  python src/analysis/copy_numbers_v3.py
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import rasterize

ROOT = Path(__file__).resolve().parents[2]
EXTRA = ROOT / "analysis" / "results_extra.json"
RESULTS = ROOT / "analysis" / "results.json"
RASTER = ROOT / "data" / "processed" / "rasters" / "lst_hot_season_median.tif"
FORESTS = ROOT / "site" / "public" / "data" / "forests.geojson"
HOURLY = ROOT / "site" / "public" / "data" / "day_of_heat_hourly.csv"
BUILTUP = ROOT / "analysis" / "tables" / "builtup_by_subcounty.csv"


def r1(v):
    return round(float(v), 1)


def forests() -> dict:
    with rasterio.open(RASTER) as src:
        hot = src.read(1).astype(float)
        if src.nodata is not None:
            hot[hot == src.nodata] = np.nan
        f = gpd.read_file(FORESTS)
        f = f[f["kind"] == "forest"].to_crs(src.crs)
        out = {}
        for name, g in f.groupby("name"):
            m = rasterize(g.geometry, out_shape=hot.shape, transform=src.transform, fill=0,
                          default_value=1, dtype="uint8").astype(bool)
            v = hot[m & np.isfinite(hot)]
            out[name] = dict(median_c=r1(np.median(v)), n_cells=int(v.size))
    q5 = json.loads(RESULTS.read_text())["q5"]["parks"]
    for name in ("Karura Forest", "Nairobi Arboretum"):
        diff = abs(out[name]["median_c"] - q5[name]["park_median_c"])
        out[name]["check_vs_q5_c"] = r1(diff)
        assert diff <= 0.3, f"{name}: {out[name]['median_c']} here, {q5[name]['park_median_c']} in q5"
    return out


def day_of_heat() -> dict:
    d = pd.read_csv(HOURLY)
    d["h"] = d.hour_eat.str[:2].astype(int)
    first = d.iloc[0]
    noon = d[d.h == 12].iloc[0]
    peak = d.loc[d.county_median_c.idxmax()]
    return dict(
        date="2026-01-27",
        first_hour=first.hour_eat, county_first_c=r1(first.county_median_c),
        county_noon_c=r1(noon.county_median_c), around_noon_c=r1(noon.around_median_c),
        rise_first_to_noon_c=r1(noon.county_median_c - first.county_median_c),
        noon_around_minus_county_c=r1(noon.around_median_c - noon.county_median_c),
        county_peak_c=r1(peak.county_median_c), county_peak_hour=peak.hour_eat,
        source="site/public/data/day_of_heat_hourly.csv",
    )


def growth() -> dict:
    t = pd.read_csv(BUILTUP)
    p = t.pivot(index="subcounty", columns="epoch", values="built_pct")
    area = t.groupby("subcounty").area_km2.first()
    added = ((p[2020] - p[1990]) / 100 * area).sort_values(ascending=False)
    change = (p[2020] - p[1990]).sort_values()
    return dict(
        added_km2_1990_2020={k: r1(v) for k, v in added.items()},
        top4_added=list(added.index[:4]),
        top4_added_share_pct=r1(100 * added.iloc[:4].sum() / added.sum()),
        under3_points_1990_2020=[k for k, v in change.items() if v < 3],
    )


def industrial_and_around(buffer_m: int = 500) -> dict:
    """Headline "in and around the Industrial Area" (Stephane, 17 November 2026): the OSM Industrial Area
    outline plus 500 m around it, against the pooled forests (results.json q2.cool_areas_median_c)."""
    areas = gpd.read_file(ROOT / "site" / "public" / "data" / "comparison_areas.geojson")
    with rasterio.open(RASTER) as src:
        hot = src.read(1).astype(float)
        if src.nodata is not None:
            hot[hot == src.nodata] = np.nan
        ind = areas[areas["name"] == "Industrial Area"].to_crs(src.crs).union_all().buffer(buffer_m)
        m = rasterize([ind], out_shape=hot.shape, transform=src.transform, fill=0, default_value=1,
                      dtype="uint8").astype(bool) & np.isfinite(hot)
        med = float(np.median(hot[m]))
    cool = json.loads(RESULTS.read_text())["q2"]["cool_areas_median_c"]
    return dict(buffer_m=buffer_m, median_c=r1(med), n_cells=int(m.sum()), forests_median_c=cool,
                gap_c=r1(med - cool))


def main() -> None:
    ex = json.loads(EXTRA.read_text())
    ex["copy_v3"] = dict(forests=forests(), industrial_and_around=industrial_and_around(), day_of_heat=day_of_heat(), growth=growth(),
                         script="src/analysis/copy_numbers_v3.py")
    EXTRA.write_text(json.dumps(ex, indent=2))
    print(json.dumps(ex["copy_v3"], indent=1))


if __name__ == "__main__":
    main()
