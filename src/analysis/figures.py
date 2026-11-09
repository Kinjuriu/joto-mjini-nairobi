"""Static figures for slides and the no-JavaScript view, in the project palette and typefaces.

Writes PNG and SVG to outputs/figures/ and copies the PNGs to site/public/figures/.
Run: uv run python -m src.analysis.figures
"""
from __future__ import annotations

import json
import shutil

import geopandas as gpd
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap  # noqa: E402

from src.analysis.layers import LST_BREAKS, load  # noqa: E402
from src.analysis.web import HEAT  # noqa: E402
from src.config import FIGURES, PROCESSED, ROOT, UTM  # noqa: E402
from src.rasterio_utils import read_grid  # noqa: E402

FONTS = ROOT / "assets" / "fonts"
for f in FONTS.glob("*.ttf"):
    font_manager.fontManager.addfont(str(f))
PAPER, INK, INK2, RULE = "#F7F4EE", "#1C1B19", "#4A4740", "#D8D2C6"
SANS, SERIF = "Source Sans 3", "Source Serif 4"
plt.rcParams.update({
    "font.family": SANS, "font.size": 11, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.edgecolor": RULE, "figure.facecolor": PAPER,
    "axes.facecolor": PAPER, "savefig.facecolor": PAPER, "svg.fonttype": "none",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
})
TABLES = ROOT / "analysis" / "tables"
SITE_FIG = ROOT / "site" / "public" / "figures"
SOURCE_LST = "Source: USGS Landsat 8 and 9 Collection 2 via Microsoft Planetary Computer; analysis Joto Mjini."


def _head(fig, title: str, subtitle: str, source: str, top: float = 0.95):
    fig.text(0.04, top, title, family=SERIF, size=17, weight="semibold", va="top")
    fig.text(0.04, top - 0.055, subtitle, size=11.5, color=INK2, va="top")
    fig.text(0.04, 0.025, source, size=9, color=INK2, va="bottom")


def _save(fig, name: str):
    for ext in ("png", "svg"):
        fig.savefig(FIGURES / f"{name}.{ext}", dpi=200 if ext == "png" else None)
    SITE_FIG.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIGURES / f"{name}.png", SITE_FIG / f"{name}.png")
    plt.close(fig)


def hero_map(res: dict):
    L = load()
    t, w, h = read_grid()
    ext = [t.c, t.c + w * t.a, t.f + h * t.e, t.f]
    county = gpd.read_file(PROCESSED / "nairobi_boundary.geojson").to_crs(UTM)
    cmap, norm = ListedColormap(HEAT), BoundaryNorm(LST_BREAKS, len(HEAT), clip=True)
    fig = plt.figure(figsize=(12, 7.6))
    ax = fig.add_axes([0.02, 0.1, 0.78, 0.74])
    a = np.where(L.county, L.hot, np.nan)
    ax.imshow(np.clip(a, LST_BREAKS[0], LST_BREAKS[-1] - 0.01), cmap=cmap, norm=norm, extent=ext,
              interpolation="nearest")
    L.wards.boundary.plot(ax=ax, color="#FFFFFF", linewidth=0.35, alpha=0.7)
    county.boundary.plot(ax=ax, color=INK, linewidth=0.9)
    minx, miny, maxx, maxy = county.total_bounds
    ax.set_xlim(minx - 800, maxx + 800); ax.set_ylim(miny - 800, maxy + 800); ax.set_axis_off()
    labels = {"Karura Forest": "Karura Forest", "Industrial Area": "Industrial Area", "Karen": "Karen",
              "Embakasi": "Embakasi", "Kibera": "Kibera", "Nairobi National Park": "Nairobi National Park",
              "Westlands": "Westlands", "Ruai": "Ruai"}
    p = gpd.read_file(ROOT / "site" / "public" / "data" / "places.geojson").to_crs(UTM)
    for _, r in p[p["name"].isin(labels)].iterrows():
        ax.plot(r.geometry.x, r.geometry.y, "s", ms=3, color=INK)
        ax.annotate(labels[r["name"]], (r.geometry.x, r.geometry.y), xytext=(5, 3), textcoords="offset points",
                    size=10, color=INK, path_effects=[matplotlib.patheffects.withStroke(linewidth=2.5, foreground=PAPER)])
    # Legend: squared swatches with hairline borders, direct value labels.
    lx = fig.add_axes([0.82, 0.3, 0.025, 0.45])
    for i, c in enumerate(HEAT):
        lx.add_patch(plt.Rectangle((0, i), 1, 1, facecolor=c, edgecolor=RULE, linewidth=0.6))
        lab = f"{LST_BREAKS[i]}" if i else f"under {LST_BREAKS[1]}"
        if i == len(HEAT) - 1:
            lab = f"{LST_BREAKS[i]} and over"
        lx.text(1.4, i + 0.5, f"{lab}" if i in (0, len(HEAT) - 1) else f"{LST_BREAKS[i]} to {LST_BREAKS[i+1]}",
                va="center", size=10)
    lx.set_xlim(0, 1); lx.set_ylim(0, len(HEAT)); lx.set_axis_off()
    lx.text(0, len(HEAT) + 0.4, "°C, surface", size=10, color=INK2)
    q = res["q1"]
    _head(fig, "On hot mornings, Nairobi's east and centre are hottest at the surface",
          f"Land surface temperature, median of {res['composites']['hot_season']['n_scenes']} clear Landsat 8 and 9 "
          f"mornings, January to March 2023 to 2026. County median {q['county_median_c']:.1f} °C.",
          SOURCE_LST + " Ward lines: geoBoundaries (Omare and Omare), CC BY 4.0. Labels © OpenStreetMap contributors.")
    _save(fig, "hero_map_hot_season")


def tree_band_chart(res: dict):
    tb = pd.read_csv(TABLES / "lst_by_tree_band.csv")
    fig = plt.figure(figsize=(9, 5.6))
    ax = fig.add_axes([0.09, 0.15, 0.86, 0.62])
    x = np.arange(len(tb))
    ax.vlines(x, tb["p25_c"], tb["p75_c"], color="#F9B06A", linewidth=9)
    ax.plot(x, tb["mean_c"], "s", ms=7, color="#A3200F")
    for i in (0, len(tb) - 1):
        ax.annotate(f"{tb['mean_c'][i]:.1f} °C", (x[i], tb["mean_c"][i]), xytext=(10, 0), textcoords="offset points",
                    va="center", size=11, weight="semibold")
    ax.annotate("Middle half of cells", (x[4], tb["p75_c"][4]), xytext=(10, -6), textcoords="offset points",
                size=10, color=INK2, va="center")
    ax.annotate("Average", (x[4], tb["mean_c"][4]), xytext=(10, 0), textcoords="offset points", size=10,
                color=INK2, va="center")
    ax.set_xticks(x, [f"{a}–{b}" for a, b in zip(tb["tree_lo"], tb["tree_hi"])])
    ax.set_xlabel("Tree cover in each 30 m cell (%)")
    ax.set_ylabel("Land surface temperature (°C)")
    ax.grid(axis="y", color=RULE, linewidth=0.6); ax.set_axisbelow(True)
    ax.tick_params(length=0)
    q = res["q3"]
    _head(fig, "The more tree cover, the cooler the ground",
          "Average land surface temperature for each band of tree cover, Nairobi County, January to March mornings 2023 to 2026.",
          SOURCE_LST + " Tree cover: ESA WorldCover 2021, CC BY 4.0.", top=0.96)
    _save(fig, "chart_tree_cover_bands")


def landcover_chart(res: dict):
    lc = pd.read_csv(TABLES / "lst_by_landcover.csv").sort_values("median_c")
    lc = lc[lc["share_pct"] >= 0.5]
    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_axes([0.27, 0.16, 0.66, 0.6])
    y = np.arange(len(lc))
    ax.barh(y, lc["median_c"], height=0.6, color="#EE7D3B")
    for yi, (_, r) in zip(y, lc.iterrows()):
        ax.text(r["median_c"] + 0.3, yi, f"{r['median_c']:.1f} °C", va="center", size=10.5)
    ax.set_yticks(y, lc["landcover"]); ax.tick_params(length=0)
    ax.set_xlim(0, lc["median_c"].max() + 5); ax.set_xticks([])
    ax.spines["bottom"].set_visible(False)
    _head(fig, "Ground under trees and water stayed coolest; open and built ground was hot",
          "Median land surface temperature by main land cover of each 30 m cell, January to March mornings 2023 to 2026.",
          SOURCE_LST + " Land cover: ESA WorldCover 2021, CC BY 4.0.", top=0.96)
    _save(fig, "chart_landcover")


def top_wards_table(res: dict):
    tw = pd.read_csv(TABLES / "top_wards.csv")
    fig = plt.figure(figsize=(8.5, 5.4))
    _head(fig, "The ten wards where people live on the hottest ground",
          "Population-weighted land surface temperature, hot-season mornings 2023 to 2026.",
          "Sources: Landsat (USGS); WorldPop 2025 (CC BY 4.0); wards geoBoundaries (CC BY 4.0).", top=0.96)
    cols = [0.05, 0.42, 0.66, 0.9]
    y0 = 0.8
    for c, txt, ha in zip(cols, ["Ward", "Surface temp. (°C)", "People", "Tree cover"],
                          ["left", "right", "right", "right"]):
        fig.text(c if ha == "left" else c - 0.02, y0, txt, size=10, color=INK2, ha=ha, weight="semibold")
    fig.add_artist(plt.Line2D([0.05, 0.92], [y0 - 0.02, y0 - 0.02], color=INK, linewidth=0.8))
    for i, r in tw.iterrows():
        yy = y0 - 0.065 * (i + 1)
        fig.text(cols[0], yy, f"{i + 1}. {r['ward_name']}", size=11)
        fig.text(cols[1] - 0.02, yy, f"{r['pop_weighted_lst_c']:.1f}", size=11, ha="right")
        fig.text(cols[2] - 0.02, yy, f"{round(r['pop_total'], -2):,.0f}", size=11, ha="right")
        fig.text(cols[3] - 0.02, yy, f"{r['tree_pct']:.0f} %", size=11, ha="right")
        fig.add_artist(plt.Line2D([0.05, 0.92], [yy - 0.02, yy - 0.02], color=RULE, linewidth=0.5))
    _save(fig, "table_top_wards")


def by_year_chart(res: dict):
    df = pd.read_csv(TABLES / "hot_season_by_year.csv")
    fig = plt.figure(figsize=(9, 5))
    ax = fig.add_axes([0.08, 0.16, 0.88, 0.56])
    full = df.set_index("year").reindex(range(df["year"].min(), df["year"].max() + 1))
    ax.plot(full.index, full["county_median_c"], color="#D2481E", linewidth=2)  # gaps stay broken
    ax.plot(df["year"], df["county_median_c"], "s", ms=6, color="#D2481E")
    for _, r in df.iterrows():
        ax.text(r["year"], r["county_median_c"] - 0.9, f"{int(r['n_scenes'])}", ha="center", size=9, color=INK2)
    ax.text(df["year"].iloc[0] - 0.2, df["county_median_c"].min() - 2.1, "Number of clear scenes under each point",
            size=9, color=INK2)
    ax.grid(axis="y", color=RULE, linewidth=0.6); ax.tick_params(length=0)
    ax.set_xticks(df["year"]); ax.set_ylabel("°C")
    ax.set_ylim(df["county_median_c"].min() - 2.5, df["county_median_c"].max() + 1.5)
    _head(fig, "Year to year, the hot-season reading jumps around",
          "County median land surface temperature, January to March composite of each year.\n"
          f"No clear trend (Mann-Kendall p = {res['q6']['mann_kendall_p']:.2f}). No composite for 2024: only one clear scene.",
          SOURCE_LST, top=0.96)
    _save(fig, "chart_hot_season_by_year")


def air_temp_chart(res: dict):
    d = pd.read_csv(TABLES / "daily_air_temp_2023_now.csv", parse_dates=["date"])
    fig = plt.figure(figsize=(11, 5))
    ax = fig.add_axes([0.06, 0.16, 0.9, 0.6])
    en_start = pd.Timestamp("2026-05-01")
    ax.axvspan(en_start, d["date"].max(), color="#ECE8E1", zorder=0)
    ax.text(en_start + pd.Timedelta(days=6), d["temperature_2m_max"].max() + 0.2, "El Niño, 2026", size=10,
            color=INK2, va="bottom")
    ax.plot(d["date"], d["temperature_2m_max"], color="#D2481E", linewidth=0.9)
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.grid(axis="y", color=RULE, linewidth=0.6); ax.tick_params(length=0); ax.set_ylabel("°C")
    _head(fig, "Hot one day, cooler the next",
          "Daily maximum air temperature for central Nairobi, 1 January 2023 to "
          f"{pd.Timestamp(res['q8']['last_date']).strftime('%-d %B %Y')}. Model data (ERA5), not a station.",
          "Source: Open-Meteo historical weather API (ERA5 reanalysis, Copernicus/ECMWF), CC BY 4.0.", top=0.96)
    _save(fig, "chart_daily_air_temp")


def main():
    FIGURES.mkdir(parents=True, exist_ok=True)
    import matplotlib.patheffects  # noqa: F401
    res = json.loads((ROOT / "analysis" / "results.json").read_text())
    for fn in (hero_map, tree_band_chart, landcover_chart, top_wards_table, by_year_chart, air_temp_chart):
        fn(res)


if __name__ == "__main__":
    main()
