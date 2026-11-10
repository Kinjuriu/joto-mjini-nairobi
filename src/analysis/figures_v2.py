"""v2 static figures for the story page.

pair_hot_cool: the hot-season and cool-season surface temperature maps side by side, on one colour scale
(the YlOrBr decile breaks of the hot season used by the web layers), for interlude 1 (layout of NASA's
paired maps). Writes outputs/figures/v2_pair_hot_cool.png and copies it to site/public/figures/.

Run: uv run python -m src.analysis.figures_v2
"""
from __future__ import annotations

import json
import shutil

import geopandas as gpd
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap

from src.analysis.figures import INK, INK2, PAPER, plt  # shared fonts and rcParams
from src.config import BOUNDARY, FIGURES, RASTERS, ROOT, UTM
from src.rasterio_utils import county_mask, read, read_grid
from src.web.tiles import YLORBR

SITE_FIG = ROOT / "site" / "public" / "figures"


def pair_hot_cool() -> None:
    hot, cool = read(RASTERS / "lst_hot_season_median.tif"), read(RASTERS / "lst_cool_season_median.tif")
    cm = county_mask()
    breaks = [round(float(v), 1) for v in np.percentile(hot[cm & np.isfinite(hot)], [10, 20, 40, 60, 80, 90])]
    t, w, h = read_grid()
    ext = [t.c, t.c + w * t.a, t.f + h * t.e, t.f]
    county = gpd.read_file(BOUNDARY).to_crs(UTM)
    res = json.loads((ROOT / "analysis" / "results.json").read_text())
    cmap = ListedColormap(YLORBR)
    lo, hi = min(np.nanmin(hot[cm]), np.nanmin(cool[cm])) - 0.1, max(np.nanmax(hot[cm]), np.nanmax(cool[cm])) + 0.1
    norm = BoundaryNorm([lo] + breaks + [hi], cmap.N)
    fig, axs = plt.subplots(1, 2, figsize=(12, 5.4), dpi=200)
    for ax, a, title in ((axs[0], hot, "January to March mornings, 2023 to 2026"),
                         (axs[1], cool, f"June to August mornings, {res['q0']['cool_first_year']} to 2026")):
        a = np.where(cm, a, np.nan)
        ax.imshow(a, extent=ext, cmap=cmap, norm=norm, interpolation="bilinear")
        county.boundary.plot(ax=ax, color=INK, lw=0.8)
        b = county.total_bounds
        ax.set_xlim(b[0] - 500, b[2] + 500)
        ax.set_ylim(b[1] - 500, b[3] + 500)
        ax.set_axis_off()
        ax.set_title(title, loc="left", fontsize=13, color=INK, fontweight="semibold")
    cax = fig.add_axes([0.25, 0.17, 0.5, 0.035])
    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal",
                      ticks=breaks, spacing="uniform")
    cb.ax.set_xticklabels([f"{v:.1f}" for v in breaks])
    cb.outline.set_linewidth(0.5)
    cb.set_label("Land surface temperature, °C (breaks at the hot-season deciles)", color=INK2, fontsize=10.5)
    fig.text(0.01, 0.015, "Data: USGS Landsat 8 and 9 Collection 2 via Microsoft Planetary Computer; "
             "analysis: Joto Mjini Nairobi.", fontsize=9, color=INK2)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.27, wspace=0.03)
    out = FIGURES / "v2_pair_hot_cool.png"
    fig.savefig(out, facecolor=PAPER)
    plt.close(fig)
    SITE_FIG.mkdir(parents=True, exist_ok=True)
    shutil.copy(out, SITE_FIG / out.name)
    print(out)


if __name__ == "__main__":
    pair_hot_cool()
