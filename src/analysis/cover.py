"""Cover image for the story (21 November 2026, D62): rooftops of the hottest and the coolest ward, side by side.

Each panel is a square of the same size (PANEL_M metres), centred on the densest square kilometre of buildings in
the ward, so both are shown at the same scale. Buildings (Overture footprints) are coloured by the hot-season
surface temperature of the 100 m around them, as the difference from the county median (the heat-diff colours
used on every map); the ground between them is ESA WorldCover 2021 land cover (trees green, grass and farmland olive), drawn
as smooth shapes; the 10 m Sentinel-2 photo used first looked blurry at this scale (D63). Wards: Kangemi, the hottest ward where people live (q4), and Karen, the
coolest ward (q1). No text is baked in; the page adds the labels so they stay readable at any width.

Run: uv run python -m src.analysis.cover
"""
from __future__ import annotations

import json

import geopandas as gpd
import matplotlib
import numpy as np
import rasterio
from rasterio.windows import from_bounds

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

from src.config import PROCESSED, RASTERS, ROOT, UTM, get_logger  # noqa: E402

log = get_logger("cover")
OUT = ROOT / "site" / "public" / "figures"
PANEL_M = 1200.0
WARDS = ("Kangemi", "Karen")
BREAKS = [-99, -6, -4, -2, -0.5, 0.5, 2, 4, 6, 99]
COLS = ["#1D4E6F", "#3B7CA6", "#8DBAD6", "#C9DDE9", "#F2EFE9", "#F6CBA6", "#F4A26B", "#D9542B", "#A1201A"]


def densest_centre(b: gpd.GeoDataFrame, ward_geom) -> tuple[float, float]:
    """Centre of the 1 km grid square (stepped by 200 m) holding the most building footprint area inside the ward."""
    c = b.geometry.centroid
    inw = c.within(ward_geom)
    x, y, a = c.x[inw].values, c.y[inw].values, b.footprint_m2[inw].values
    best, bxy = -1, None
    x0, y0, x1, y1 = ward_geom.bounds
    for cx in np.arange(x0 + 500, x1 - 499, 200):
        for cy in np.arange(y0 + 500, y1 - 499, 200):
            m = (abs(x - cx) < 500) & (abs(y - cy) < 500)
            s = a[m].sum()
            if s > best:
                best, bxy = s, (cx, cy)
    if bxy is None:   # ward smaller than 1 km: use its centroid
        bxy = (ward_geom.centroid.x, ward_geom.centroid.y)
    return bxy


def main() -> dict:
    wards = gpd.read_file(PROCESSED / "nairobi_wards.geojson").to_crs(UTM).set_index("ward_name")
    b = gpd.read_parquet(PROCESSED / "buildings_lst.parquet").to_crs(UTM)
    out = {}
    fig, axes = plt.subplots(1, 2, figsize=(16, 8), dpi=150)
    fig.subplots_adjust(0, 0, 1, 1, wspace=0.012)
    fig.patch.set_facecolor("#0B1620")
    cmap, norm = ListedColormap(COLS), BoundaryNorm(BREAKS, len(COLS))
    if True:
        for ax, ward in zip(axes, WARDS):
            cx, cy = densest_centre(b, wards.loc[ward].geometry)
            h = PANEL_M / 2
            box = (cx - h, cy - h, cx + h, cy + h)
            # Ground: ESA WorldCover 2021 (10 m) drawn as smooth shapes, which stay sharp at this scale where the 10 m
            # Sentinel-2 photo looked blurry (21 Nov, D63): trees green, grass and farmland olive, the rest dark.
            with rasterio.open(RASTERS / "worldcover_2021.tif") as wc:
                cls = wc.read(1, window=from_bounds(*box, wc.transform), boundless=True, fill_value=0)
            from scipy.ndimage import gaussian_filter, zoom
            ground = np.zeros((*cls.shape, 3)) + np.array([0x1A, 0x1F, 0x1C]) / 255
            for code, col in ((30, "#33402C"), (40, "#33402C"), (10, "#2F6B3F"), (80, "#24476B")):
                m = gaussian_filter(zoom((cls == code).astype(float), 8, order=1), 5) > 0.5   # smooth edges
                if code == 30:
                    ground = np.repeat(np.repeat(ground, 8, 0), 8, 1)
                rgb = np.array([int(col[i:i + 2], 16) for i in (1, 3, 5)]) / 255
                ground[m[:ground.shape[0], :ground.shape[1]]] = rgb
            ax.imshow(ground, extent=(box[0], box[2], box[1], box[3]), interpolation="antialiased")
            sel = b.cx[box[0]:box[2], box[1]:box[3]]
            sel.plot(ax=ax, column="lst_anomaly_c", cmap=cmap, norm=norm, linewidth=0.2, edgecolor="#101418")
            ax.set_xlim(box[0], box[2]); ax.set_ylim(box[1], box[3]); ax.set_axis_off()
            # 200 m scale bar, bottom left
            ax.plot([box[0] + 60, box[0] + 260], [box[1] + 60, box[1] + 60], color="white", lw=3, solid_capstyle="butt")
            ax.text(box[0] + 60, box[1] + 85, "200 m", color="white", fontsize=12, fontweight="bold")
            lon, lat = gpd.GeoSeries.from_xy([cx], [cy], crs=UTM).to_crs(4326).iloc[0].coords[0]
            out[ward] = dict(centre_lonlat=[round(lon, 5), round(lat, 5)], n_buildings=int(len(sel)),
                             median_building_lst_c=round(float(sel.lst_c.median()), 1),
                             median_building_diff_c=round(float(sel.lst_anomaly_c.median()), 1))
    for ext in ("webp", "png"):
        fig.savefig(OUT / f"cover_rooftops.{ext}", facecolor=fig.get_facecolor(), dpi=150 if ext == "webp" else 100)
    plt.close(fig)
    # The story's two rooftop map steps (Eastlands and Karen): buildings in the same 1.2 km square around each
    # camera centre, and the census iron-sheet share of the census sub-county the centre falls in (D62).
    import pandas as pd
    views = {"eastlands": (36.9115, -1.2770), "karen": tuple(out["Karen"]["centre_lonlat"])}
    ws = pd.read_csv(ROOT / "analysis" / "tables" / "ward_population_scaled.csv").set_index("ward_name")
    roofs = pd.read_csv(ROOT / "data" / "raw" / "census_2019" / "kenya_2019_census_roofing_material_by_county_subcounty.csv")
    roofs = roofs[(roofs.county == "NAIROBI CITY") & (roofs.breakdown == "all") & (roofs.level == "subcounty")].set_index("name")
    vout = {}
    for k, (lon, lat) in views.items():
        pt = gpd.GeoSeries.from_xy([lon], [lat], crs=4326).to_crs(UTM).iloc[0]
        h = PANEL_M / 2
        sel = b.cx[pt.x - h:pt.x + h, pt.y - h:pt.y + h]
        ward = wards[wards.contains(pt)].index[0]
        sc = ws.loc[ward, "census_subcounty"]
        vout[k] = dict(centre_lonlat=[lon, lat], ward=ward, census_subcounty=sc.title().replace("'A", "'a"), n_buildings=int(len(sel)),
                       median_building_lst_c=round(float(sel.lst_c.median()), 1),
                       median_building_diff_c=round(float(sel.lst_anomaly_c.median()), 1),
                       share_hotter_than_median_pct=round(float(100 * (sel.lst_anomaly_c > 0).mean()), 1),
                       iron_sheet_households_pct=round(float(roofs.loc[sc, "iron_sheets_pct"]), 1))
    extra = json.loads((ROOT / "analysis" / "results_extra.json").read_text())
    extra["cover"] = dict(panel_m=PANEL_M, wards=out, views=vout,
                          gap_c=round(out["Kangemi"]["median_building_lst_c"] - out["Karen"]["median_building_lst_c"], 1), note="Buildings coloured by hot-season LST of the surrounding 100 m, difference from the county median; Sentinel-2 2026 underneath (D62)")
    (ROOT / "analysis" / "results_extra.json").write_text(json.dumps(extra, indent=2))
    log.info("cover: %s", out)
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
