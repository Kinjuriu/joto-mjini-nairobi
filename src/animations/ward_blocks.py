"""Ward block charts in the style of NASA's TEMPO plots (Stephane's request, 11 November 2026).

Two figures: the ten hottest and the ten coolest wards where people live (ranked by population-weighted
hot-season land surface temperature). Each ward is drawn as its own block, filled with the 30 m land surface
temperature of clear January to March mornings 2023 to 2026, on ONE colour scale shared by both figures, so a
hot ward and a cool ward can be compared directly. Purple-to-yellow ramp (matplotlib "plasma"): purple is
cooler ground, yellow the hottest. Each ward is drawn at its own scale, with a 1 km bar in each block.

Run: python3 -m src.animations.ward_blocks
Outputs: outputs/figures/wards_hottest.png, wards_coolest.png, copied to site/public/figures/.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from rasterio.features import rasterize
from rasterio.transform import from_bounds
from rasterio.warp import Resampling

from src.animations.render_nasa import INK, INK2, ROOT, to_grid

for f in ("SourceSans3-Regular.ttf", "SourceSans3-Semibold.ttf"):
    font_manager.fontManager.addfont(str(ROOT / "assets" / "fonts" / f))
plt.rcParams.update({"font.family": "Source Sans 3"})
SITE = ROOT / "site" / "public"
LST = ROOT / "data" / "processed" / "rasters" / "lst_hot_season_median.tif"
VMIN, VMAX = 28, 48
CMAP = plt.get_cmap("plasma").copy()
CMAP.set_bad("#FFFFFF", 0)


def rings(geom):
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [np.asarray(r) for p in polys for r in p]


def bounds_of(geom, pad=0.08):
    xs = np.concatenate([r[:, 0] for r in rings(geom)])
    ys = np.concatenate([r[:, 1] for r in rings(geom)])
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    # Square box around the ward, so every block has the same shape.
    cx, cy, half = (x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0) / 2 * (1 + pad)
    return cx - half, cy - half, cx + half, cy + half


def panel(ax, f):
    p, g = f["properties"], f["geometry"]
    b = bounds_of(g)
    n = 300
    a = to_grid(LST, b, n, n, resampling=Resampling.bilinear)
    inside = rasterize([(g, 1)], out_shape=(n, n), transform=from_bounds(*b, n, n), fill=0) == 1
    a = np.where(inside, a, np.nan)
    im = ax.imshow(a, extent=(b[0], b[2], b[1], b[3]), origin="upper", cmap=CMAP, vmin=VMIN, vmax=VMAX, interpolation="bilinear")
    for r in rings(g):
        ax.plot(r[:, 0], r[:, 1], color=INK, lw=1.2)
    ax.set_xlim(b[0], b[2]); ax.set_ylim(b[1], b[3]); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#C9CFD6"); s.set_linewidth(0.8)
    # 1 km bar (1 km is about 0.009 degrees at Nairobi's latitude).
    km = 1 / 111.32
    w = b[2] - b[0]
    L = km if km < 0.45 * w else km / 2
    x0, y0 = b[0] + 0.05 * w, b[1] + 0.05 * w
    ax.plot([x0, x0 + L], [y0, y0], color=INK, lw=2.2, solid_capstyle="butt")
    ax.text(x0 + L / 2, y0 + 0.025 * w, "1 km" if L == km else "500 m", ha="center", va="bottom", fontsize=10.5, color=INK)
    ax.set_title(p["ward_name"], fontsize=15, fontweight="semibold", color=INK, loc="left", pad=22)
    ax.text(0, 1.02, f"{p['pop_weighted_lst_c']:.1f} °C where people live · trees {p['tree_pct']:.0f} %",
            transform=ax.transAxes, fontsize=11.5, color=INK2, va="bottom")
    return im


def figure(feats, title, subtitle, out):
    cols, rows = 5, math.ceil(len(feats) / 5)
    H = 3.75 * rows + 2.9
    fig = plt.figure(figsize=(16, H), dpi=110, facecolor="white")
    fig.text(0.03, 1 - 0.55 / H, title, fontsize=26, fontweight="semibold", color=INK, va="top")
    fig.text(0.03, 1 - 1.05 / H, subtitle, fontsize=15, color=INK2, va="top")
    top, bottom = 1 - 1.95 / H, 1.45 / H
    gs = fig.add_gridspec(rows, cols, left=0.03, right=0.97, top=top, bottom=bottom, wspace=0.12, hspace=0.32)
    im = None
    for i, f in enumerate(feats):
        im = panel(fig.add_subplot(gs[i // cols, i % cols]), f)
    cax = fig.add_axes([0.3, 0.9 / H, 0.4, 0.16 / H])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal", extend="both", ticks=range(VMIN, VMAX + 1, 4))
    cb.set_label("Land surface temperature, clear January to March mornings, 2023 to 2026 (°C)", fontsize=13, color=INK)
    cb.ax.tick_params(labelsize=12)
    fig.text(0.03, 0.14 / H, "Data: USGS Landsat 8 and 9 via Microsoft Planetary Computer; WorldPop 2025; ESA WorldCover 2021; IEBC ward boundaries. "
             "Each ward drawn at its own scale. Graphic: Joto Mjini Nairobi.", fontsize=11, color=INK2)
    for d in (ROOT / "outputs" / "figures", SITE / "figures"):
        d.mkdir(parents=True, exist_ok=True)
        fig.savefig(d / out, dpi=110, facecolor="white")
    plt.close(fig)
    print(out)


def main():
    g = json.loads((SITE / "data" / "wards.geojson").read_text())
    ok = [f for f in g["features"] if f["properties"].get("pop_weighted_lst_c") is not None]
    ok.sort(key=lambda f: -f["properties"]["pop_weighted_lst_c"])
    sub = "Land surface temperature inside each ward on hot mornings. Same colour scale in both charts: purple is cooler ground, yellow the hottest."
    figure(ok[:10], "The ten hottest wards where people live", sub, "wards_hottest.png")
    figure(ok[-10:][::-1], "The ten coolest wards where people live", sub, "wards_coolest.png")
    json.dump({"hottest": [f["properties"]["ward_name"] for f in ok[:10]], "coolest": [f["properties"]["ward_name"] for f in ok[-10:][::-1]]},
              open(ROOT / "outputs" / "figures" / "ward_blocks.json", "w"), indent=1)


if __name__ == "__main__":
    main()
