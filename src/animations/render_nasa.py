"""Data-visualisation animations in the style of NASA's HRRR wind-gust and TEMPO NO2 animations
(Stephane's request, 10 November 2026): a plain scientific map on white, a title at the top left, a
"Valid:" time stamp at the top right, latitude and longitude on the axes, the county and ward outlines,
a colour bar with units at the bottom and a credit line. No satellite photo underneath.

Colours: a blue-to-red diverging ramp whose cool end is rgb(62,77,183) (#3E4DB7), close to matplotlib's
"coolwarm", for temperatures; white to #3E4DB7 for built-up land.

Animations (outputs in outputs/animations/nasa/ and site/public/media/, same names the page already uses):
  day       day_of_heat     27 January 2026, 06:00 to 19:00, CLMS hourly land surface temperature (about 3 km),
                            Nairobi region. Raw hourly values, no sharpening.
  mornings  hot_mornings    every clear January to March Landsat morning 2014 to 2026, difference from that
                            morning's county median, 30 m
  growth    nairobi_grows   GHSL built-up share, 1975 to 2025

Runs with plain Python (numpy, pandas, matplotlib, rasterio, imageio, imageio-ffmpeg, Pillow); no geopandas.
Run: python3 -m src.animations.render_nasa [day mornings growth]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import imageio.v2 as imageio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib import font_manager, patheffects
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "animations" / "nasa"
MEDIA = ROOT / "site" / "public" / "media"
SITE = ROOT / "site" / "public" / "data"
W, H, DPI = 1600, 1000, 100

for f in ("SourceSans3-Regular.ttf", "SourceSans3-Semibold.ttf"):
    font_manager.fontManager.addfont(str(ROOT / "assets" / "fonts" / f))
plt.rcParams.update({"font.family": "Source Sans 3", "font.size": 15, "axes.edgecolor": "#1C2530",
                     "xtick.color": "#1C2530", "ytick.color": "#1C2530", "axes.linewidth": 1.0})
INK = "#1C2530"
INK2 = "#4A5563"
# Diverging ramp, cool end rgb(62,77,183); shaped like matplotlib's coolwarm.
COOLWARM = LinearSegmentedColormap.from_list("joto_coolwarm", [
    (0.0, "#3E4DB7"), (0.17, "#6788EE"), (0.34, "#9ABBFF"), (0.5, "#EDEDED"),
    (0.66, "#F7A889"), (0.83, "#E26952"), (1.0, "#B40426")])
COOLWARM.set_bad("#FFFFFF", 0)
BUILT = LinearSegmentedColormap.from_list("joto_built", ["#FFFFFF", "#C8CDEE", "#8A93D8", "#3E4DB7", "#1E2766"])
BUILT.set_bad("#FFFFFF", 0)
LABELS = ["Westlands", "Karura Forest", "Industrial Area", "Kibera", "Karen", "Kasarani", "Dandora", "Ruai",
          "Nairobi National Park"]
HALO = [patheffects.withStroke(linewidth=3, foreground="white")]


def lines(path: Path):
    g = json.loads(path.read_text())
    out = []
    for f in g["features"]:
        geom = f["geometry"]
        polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
        for p in polys:
            for ring in p:
                a = np.asarray(ring)
                out.append((a[:, 0], a[:, 1]))
    return out


COUNTY = lines(SITE / "county.geojson")
WARDS = lines(SITE / "wards.geojson")
PLACES = {f["properties"]["name"]: f["geometry"]["coordinates"] for f in json.loads((SITE / "places.geojson").read_text())["features"]}


def to_grid(path: Path, bounds, w: int, h: int, band=1, resampling=Resampling.bilinear) -> np.ndarray:
    """Reproject a raster onto a regular latitude-longitude grid."""
    dst = from_bounds(*bounds, w, h)
    with rasterio.open(path) as s:
        a = s.read(band).astype("float32")
        if s.nodata is not None and not np.isnan(s.nodata):
            a[a == s.nodata] = np.nan
        out = np.full((h, w), np.nan, dtype="float32")
        reproject(a, out, src_transform=s.transform, src_crs=s.crs, dst_transform=dst, dst_crs="EPSG:4326",
                  resampling=resampling, src_nodata=np.nan, dst_nodata=np.nan)
    return out


class Frame:
    """One figure reused for every frame: only the image, the time stamp and the counter change."""

    def __init__(self, title, subtitle, credit, bounds, cmap, vmin, vmax, cb_label, cb_ticks, cb_ticklabels=None,
                 extend="both", interpolation="bilinear", labels=LABELS, wards=True, nodata_note=None):
        self.fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor="white")
        f = self.fig
        f.text(0.035, 0.945, title, fontsize=27, fontweight="semibold", color=INK, va="baseline")
        f.text(0.035, 0.905, subtitle, fontsize=17, color=INK2, va="baseline")
        self.valid = f.text(0.965, 0.945, "", fontsize=24, fontweight="semibold", color=INK, ha="right", va="baseline")
        self.sub = f.text(0.965, 0.905, "", fontsize=18, color=INK, ha="right", va="baseline", fontweight="semibold")
        f.text(0.035, 0.016, credit, fontsize=12.5, color=INK2, va="baseline")
        ax = f.add_axes([0.06, 0.17, 0.88, 0.70])
        x0, y0, x1, y1 = bounds
        self.im = ax.imshow(np.full((10, 10), np.nan), extent=(x0, x1, y0, y1), origin="upper", cmap=cmap, vmin=vmin,
                            vmax=vmax, interpolation=interpolation, zorder=1)
        if wards:
            for x, y in WARDS:
                ax.plot(x, y, color="#5A6370", lw=0.35, alpha=0.55, zorder=2)
        for x, y in COUNTY:
            ax.plot(x, y, color=INK, lw=1.8, zorder=3)
        for n in labels:
            if n in PLACES:
                lx, ly = PLACES[n]
                if x0 < lx < x1 and y0 < ly < y1:
                    ax.text(lx, ly, n, fontsize=13, color=INK, ha="center", va="center", path_effects=HALO, zorder=4)
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        fmt_x = lambda v, _: f"{v:.1f}°E"
        fmt_y = lambda v, _: f"{abs(v):.1f}°S" if v < 0 else f"{v:.1f}°N"
        ax.xaxis.set_major_formatter(fmt_x)
        ax.yaxis.set_major_formatter(fmt_y)
        ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.1))
        ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.1))
        ax.tick_params(labelsize=12.5, length=4)
        ax.grid(color="#9AA3AE", lw=0.4, alpha=0.5, zorder=0)
        self.ax = ax
        cax = f.add_axes([0.28, 0.105, 0.44, 0.022])
        cb = f.colorbar(self.im, cax=cax, orientation="horizontal", extend=extend, ticks=cb_ticks)
        if cb_ticklabels:
            cb.ax.set_xticklabels(cb_ticklabels)
        cb.ax.tick_params(labelsize=13)
        cb.outline.set_linewidth(0.8)
        cb.set_label(cb_label, fontsize=15, color=INK, labelpad=4)
        if nodata_note:
            f.patches.append(matplotlib.patches.Rectangle((0.75, 0.105), 0.018, 0.022, transform=f.transFigure,
                                                          facecolor="white", edgecolor=INK, lw=0.8))
            f.text(0.773, 0.116, nodata_note, fontsize=13, color=INK2, va="center")
        self.counter = f.text(0.965, 0.87, "", fontsize=17, color=INK, ha="right", va="baseline", fontweight="semibold")

    def render(self, data, valid, sub="", counter="") -> np.ndarray:
        self.im.set_data(data)
        self.valid.set_text(valid)
        self.sub.set_text(sub)
        self.counter.set_text(counter)
        self.fig.canvas.draw()
        return np.asarray(self.fig.canvas.buffer_rgba())[..., :3].copy()


def write(name, frames, fps, poster, hold_last_s=2.0) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    frames = frames + [frames[-1]] * int(round(hold_last_s * fps))
    mp4, webm, gif, png = (OUT / f"{name}{s}" for s in (".mp4", ".webm", ".gif", "_poster.png"))
    with imageio.get_writer(mp4, fps=fps, codec="libx264", quality=8, pixelformat="yuv420p", macro_block_size=8,
                            ffmpeg_params=["-preset", "veryfast"]) as w:
        for fr in frames:
            w.append_data(fr)
    with imageio.get_writer(webm, fps=fps, codec="libvpx-vp9", pixelformat="yuv420p", macro_block_size=8,
                            ffmpeg_params=["-b:v", "0", "-crf", "34", "-deadline", "realtime", "-cpu-used", "8"]) as w:
        for fr in frames:
            w.append_data(fr)
    Image.fromarray(frames[poster]).save(png, optimize=True)
    # GIF for LinkedIn: 960 px wide, adaptive palette, 8 MB or less.
    for width in (960, 800, 640):
        ims = [Image.fromarray(fr).resize((width, int(width * H / W)), Image.LANCZOS).convert("P", palette=Image.ADAPTIVE, colors=128)
               for fr in frames]
        ims[0].save(gif, save_all=True, append_images=ims[1:], duration=int(1000 / fps), loop=0, optimize=True)
        if gif.stat().st_size <= 8e6:
            break
    for p in (mp4, webm, gif, png):
        (MEDIA / p.name).write_bytes(p.read_bytes())
    sizes = {p.suffix: round(p.stat().st_size / 1e6, 2) for p in (mp4, webm, gif, png)}
    print(name, len(frames), "frames", sizes)
    return dict(frames=len(frames), fps=fps, sizes_mb=sizes)


# ---------------------------------------------------------------- 1. a day of heat, regional
def day() -> dict:
    folder = next((ROOT / "data" / "raw" / "clms_lst").glob("2026-*"))
    meta = json.loads((folder / "meta.json").read_text())
    bounds = (36.5, -1.55, 37.25, -1.08)
    fr = Frame("Land surface temperature, Nairobi region",
               "Copernicus hourly land surface temperature, about 3 km. One clear hot-season day.",
               "Data: Copernicus Land Monitoring Service, Global Land Surface Temperature hourly v3, via the Copernicus Data Space Ecosystem. "
               "Graphic: Joto Mjini Nairobi.",
               bounds, COOLWARM, 10, 55, "Land surface temperature (°C)", [10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
               labels=["Westlands", "Karura Forest", "Industrial Area", "Karen", "Ruai", "Nairobi National Park"],
               wards=False, nodata_note="No data (cloud)")
    frames, stamps, valid = [], [], []
    w, h = 750, 470
    for f in sorted(folder.glob("lst_*utc.tif")):
        hr = int(f.stem[4:6])
        a = to_grid(f, bounds, w, h, resampling=Resampling.bilinear)
        eat = (hr + 3) % 24
        d = pd.Timestamp(meta["date"])
        frames.append(fr.render(a, f"Valid: {d.day} {d:%b %Y}, {eat:02d}:00 EAT", f"{hr:02d}:00 UTC"))
        stamps.append(eat)
        valid.append(float(np.isfinite(a).mean()) if 10 <= eat <= 15 else 0.0)
    poster = int(np.argmax(valid))   # the clearest hour around midday
    info = write("day_of_heat", frames, fps=1.5, poster=poster)
    plt.close(fr.fig)
    return info


# ---------------------------------------------------------------- 2. every clear hot-season morning
def mornings() -> dict:
    cat = pd.read_csv(ROOT / "data" / "processed" / "landsat_scene_catalogue.csv")
    cat["month"] = cat["date"].str[5:7].astype(int)
    cat["year"] = cat["date"].str[:4].astype(int)
    sel = cat[cat["usable"] & cat["month"].isin([1, 2, 3]) & cat["year"].between(2014, 2026)].sort_values("date")
    bounds = (36.64, -1.46, 37.12, -1.155)
    w, h = 1200, 762
    county = to_grid_mask(bounds, w, h)
    fr = Frame("Every clear hot-season morning, 2014 to 2026",
               "Land surface temperature on each clear January to March morning, difference from that morning's county median",
               "Data: USGS Landsat 8 and 9 Collection 2 Level-2, via Microsoft Planetary Computer. Graphic: Joto Mjini Nairobi.",
               bounds, COOLWARM, -8, 8, "Difference from the county median that morning (°C)", [-8, -6, -4, -2, 0, 2, 4, 6, 8],
               ["−8", "−6", "−4", "−2", "0", "+2", "+4", "+6", "+8"], nodata_note="No data (cloud)")
    frames, dates = [], []
    for _, r in sel.iterrows():
        p = ROOT / "data" / "interim" / "landsat" / f"{r.scene_id}_lst_c.tif"
        if not p.exists():
            continue
        v = to_grid(p, bounds, w, h)
        ok = county & np.isfinite(v)
        if ok.sum() < 0.5 * county.sum():
            continue
        d = np.where(ok, v - np.nanmedian(v[ok]), np.nan)
        ts = pd.Timestamp(r.datetime_nairobi)
        frames.append(fr.render(d, f"Valid: {ts.day} {ts:%b %Y}, {ts:%H:%M} EAT", f"County median {np.nanmedian(v[ok]):.1f} °C"))
        dates.append(r.date)
    poster = dates.index("2026-01-27") if "2026-01-27" in dates else len(frames) - 1
    info = write("hot_mornings", frames, fps=2, poster=poster)
    info.update(n_scenes=len(dates), first=dates[0], last=dates[-1])
    plt.close(fr.fig)
    return info


def to_grid_mask(bounds, w, h) -> np.ndarray:
    from rasterio.features import rasterize
    g = json.loads((SITE / "county.geojson").read_text())
    return rasterize([(f["geometry"], 1) for f in g["features"]], out_shape=(h, w), transform=from_bounds(*bounds, w, h), fill=0) == 1


# ---------------------------------------------------------------- 3. Nairobi grows
def growth() -> dict:
    epochs = [1975, 1990, 2000, 2010, 2020, 2025]
    km2 = pd.read_csv(ROOT / "analysis" / "tables" / "ghsl_built_by_epoch.csv").set_index("epoch")["built_km2"]
    bounds = (36.64, -1.46, 37.12, -1.155)
    w, h = 600, 381
    county = to_grid_mask(bounds, w, h)
    fr = Frame("Nairobi grows, 1975 to 2025",
               "Share of the ground covered by buildings, Global Human Settlement Layer, about 100 m",
               "Data: European Commission, Joint Research Centre, GHS-BUILT-S R2023A (2025 is a projection). Graphic: Joto Mjini Nairobi.",
               bounds, BUILT, 0, 60, "Built-up share of each cell (%)", [0, 10, 20, 30, 40, 50, 60], extend="max",
               interpolation="nearest")
    grids = {y: np.where(county, to_grid(ROOT / "data" / "processed" / "rasters" / f"ghsl_built_{y}.tif", bounds, w, h,
                                         resampling=Resampling.nearest) * 100, np.nan) for y in epochs}
    frames = []
    hold, fades = 6, 5
    for i, y in enumerate(epochs):
        lab = f"Valid: {y}" + (" (projection)" if y == 2025 else "")
        for _ in range(hold):
            frames.append(fr.render(grids[y], lab, f"Built-up: about {km2[y]:.0f} km²"))
        if i + 1 < len(epochs):
            n = epochs[i + 1]
            for k in range(1, fades + 1):
                t = k / (fades + 1)
                frames.append(fr.render((1 - t) * grids[y] + t * grids[n], lab, f"Built-up: about {(1 - t) * km2[y] + t * km2[n]:.0f} km²"))
    info = write("nairobi_grows", frames, fps=4, poster=len(frames) - 1)
    plt.close(fr.fig)
    return info


if __name__ == "__main__":
    todo = sys.argv[1:] or ["day", "mornings", "growth"]
    res = {k: {"day": day, "mornings": mornings, "growth": growth}[k]() for k in todo}
    (OUT / "render_nasa.json").write_text(json.dumps(res, indent=1, default=str))
