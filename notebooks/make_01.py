"""Writes notebooks/01_data_pipeline.ipynb. Run: uv run python notebooks/make_01.py"""
import nbformat as nbf

md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
cells = [
md("""# 01. Data pipeline for Joto Mjini

This notebook runs the pipeline in `src/pipeline/` step by step and shows a quick look at each output. Each step skips work that is already done, so running the notebook again is fast. To rebuild a step from scratch, run its script with `--force`, for example `uv run python -m src.pipeline.s2_landsat --force`.

Every dataset is listed with its licence and citation in `data/SOURCES.md`."""),
code("""import sys, os
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
os.chdir(ROOT); sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd, geopandas as gpd, matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from src.config import RASTERS, PROCESSED, UTM
from src.rasterio_utils import read, read_grid, county_mask
plt.rcParams.update({"figure.dpi": 110, "font.family": "sans-serif", "axes.titlelocation": "left"})"""),
md("""## Step 1. Study area, wards and place names

Nairobi County comes from geoBoundaries (ADM1). The 85 wards come from geoBoundaries ADM3, which is based on the Kenya County Assembly Boundaries by B. A. Omare and G. Omare. Place names, parks and forests come from OpenStreetMap."""),
code("""from src.pipeline import s1_boundaries
s1_boundaries.main()
county = gpd.read_file(PROCESSED / "nairobi_boundary.geojson").to_crs(UTM)
wards = gpd.read_file(PROCESSED / "nairobi_wards.geojson").to_crs(UTM)
print(f"County area {county.area.sum()/1e6:.1f} km2; {len(wards)} wards covering {wards.area.sum()/1e6:.1f} km2")
ax = wards.plot(facecolor="#F7F4EE", edgecolor="#8C8475", linewidth=0.4, figsize=(9, 6))
county.boundary.plot(ax=ax, color="#1C1B19", linewidth=1)
ax.set_title("Nairobi County and its 85 wards"); ax.set_axis_off()"""),
md("""## Step 2. Landsat surface temperature

We search every Landsat 8 and 9 scene over Nairobi since April 2013 on Microsoft Planetary Computer, mask clouds with the `qa_pixel` band, convert the surface temperature band to °C, and keep a scene as usable when at least 80 % of the county is clear. Composites are the median of usable scenes, pixel by pixel.

This is **land surface temperature**: how hot the ground, roofs and roads are, measured at about 100 m. It is different from the air temperature people feel."""),
code("""from src.pipeline import s2_landsat, s2b_composites
cat = s2_landsat.main()
meta = s2b_composites.main()
print(f"{len(cat)} scenes, {int(cat.usable.sum())} usable")
print("Hot season:", meta["hot_season"]["n_scenes"], "scenes from", meta["hot_season"]["first_year"])
print("Cool season:", meta["cool_season"]["n_scenes"], "scenes from", meta["cool_season"]["first_year"])
print("Hottest clear day:", meta["hottest_clear_day"])"""),
md("### The scene catalogue (usable scenes)"),
code("""cat[cat.usable][["scene_id", "datetime_nairobi", "clear_fraction_county", "lst_median_c", "lst_p10_c", "lst_p90_c"]].tail(25)"""),
md("""### Quick look: hot-season surface temperature

Fixed colour breaks (the same breaks used on the website), so maps from different seasons can be compared directly."""),
code("""BREAKS = [24, 28, 32, 35, 38, 41, 44, 48]
HEAT = ["#FFF5E6", "#FDD9A8", "#F9B06A", "#EE7D3B", "#D2481E", "#A3200F", "#6B0F0A"]
cmap, norm = ListedColormap(HEAT), BoundaryNorm(BREAKS, len(HEAT))
t, w, h = read_grid()
ext = [t.c, t.c + w * t.a, t.f + h * t.e, t.f]
fig, axs = plt.subplots(1, 2, figsize=(13, 5))
for ax, name in zip(axs, ["hot_season", "cool_season"]):
    a = read(RASTERS / f"lst_{name}_median.tif")
    im = ax.imshow(a, cmap=cmap, norm=norm, extent=ext)
    county.boundary.plot(ax=ax, color="#1C1B19", linewidth=0.8)
    ax.set_title(f"Land surface temperature, {name.replace('_', ' ')} median (°C)"); ax.set_axis_off()
fig.colorbar(im, ax=axs, shrink=0.7, ticks=BREAKS)"""),
md("""## Step 3. Land cover, population, buildings and built-up growth

ESA WorldCover 2021 (10 m), WorldPop 2025 constrained population (100 m), Overture building footprints and GHSL built-up surface (1975 to 2025)."""),
code("""from src.pipeline import s3_context
s3_context.main()
wc = read(RASTERS / "worldcover_majority_30m.tif")
codes = [10, 20, 30, 40, 50, 60, 80, 90]
cols = ["#2E6B3F", "#9DB36B", "#D9D59A", "#E8C26A", "#C2401A", "#CFC6B4", "#2F6B8F", "#7FB0A8"]
names = ["Tree cover", "Shrubland", "Grassland", "Cropland", "Built-up", "Bare", "Water", "Wetland"]
lut = np.full(256, np.nan); [lut.__setitem__(c, i) for i, c in enumerate(codes)]
idx = lut[np.nan_to_num(wc, nan=0).astype(int)]
fig, ax = plt.subplots(figsize=(9, 6))
ax.imshow(idx, cmap=ListedColormap(cols), vmin=-0.5, vmax=len(codes) - 0.5, extent=ext, interpolation="nearest")
county.boundary.plot(ax=ax, color="#1C1B19", linewidth=0.8); ax.set_axis_off()
ax.set_title("Main land cover in each 30 m cell, ESA WorldCover 2021")
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=c, label=n) for c, n in zip(cols, names)], loc="lower left", fontsize=8, frameon=False)
cm = county_mask()
print("Share of county:", {n: f"{100*(wc[cm]==c).mean():.1f}%" for c, n in zip(codes, names)})
pop = read(RASTERS / "population_30m.tif"); print(f"WorldPop 2025 county total on 30 m grid: {np.nansum(pop[cm]):,.0f}")
b = pd.read_parquet(PROCESSED / "nairobi_buildings.parquet", columns=["source"]); print(f"Buildings: {len(b):,}")"""),
md("## Steps 4 and 5. Daily air temperature and the El Niño index"),
code("""from src.pipeline import s4_climate
s4_climate.main()
air = pd.read_csv(PROCESSED / "nairobi_daily_air_temp.csv", parse_dates=["date"])
roni = pd.read_csv(PROCESSED / "roni.csv").dropna()
print(air.tail(3)); print(roni.tail(6))"""),
md("""## Step 7 and 8. Basemap and manifest

The Protomaps basemap extract is in `site/public/data/nairobi_basemap.pmtiles`. The manifest lists every processed file."""),
code("""from src.pipeline import manifest
manifest.main()
print((PROCESSED / "MANIFEST.md").read_text()[:1500])"""),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3"}})
nbf.write(nb, "notebooks/01_data_pipeline.ipynb")
