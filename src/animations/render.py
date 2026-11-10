"""v2 animated maps (chunk 4), in the spirit of NASA's wind-gust animation: title, large time stamp,
colour bar and credit baked into every frame; a faded Sentinel-2 true-colour background; county outline,
faint ward lines and a few place labels.

Animations:
  mornings    every clear January to March Landsat morning, 2014 to 2026, difference from that morning's median
  growth      GHSL built-up surface, 1975 to 2025, with cross-fades and a built-up area counter
  day         a day of heat, 27 January 2026: CLMS hourly LST sharpened with the same morning's Landsat scene

Outputs per animation in outputs/animations/ and site/public/media/: <name>.mp4 (H.264), <name>.webm (VP9),
<name>.gif (8 MB or less) and <name>_poster.png. Videos are written through imageio with imageio-ffmpeg.

Run: uv run python -m src.animations.render [mornings growth day]
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import geopandas as gpd
import imageio.v2 as imageio
import numpy as np
import pandas as pd
import rasterio
from PIL import Image
from rasterio.transform import Affine, from_bounds
from rasterio.warp import Resampling, reproject

from src.analysis.figures import INK, INK2, PAPER, plt
from src.config import BOUNDARY, INTERIM, PROCESSED, RASTERS, RAW, ROOT, UTM, WARDS, get_logger
from src.web.tiles import DIFF_BREAKS, DIFF_COLOURS, GHSL_BREAKS, GHSL_COLOURS, YLORBR, _rgb

log = get_logger("animations")
OUT = ROOT / "outputs" / "animations"
MEDIA = ROOT / "site" / "public" / "media"
EXTRA = ROOT / "analysis" / "results_extra.json"
W, H = 1600, 1000
MAP_BOX = (0.0, 0.155, 1.0, 0.745)    # left, bottom, width, height of the map in figure fractions
S2_CREDIT = "Background: contains modified Copernicus Sentinel data 2026, processed by Joto Mjini Nairobi"
LABELS = ["Westlands", "Karura Forest", "Industrial Area", "Kibera", "Karen", "Kasarani", "Embakasi",
          "Nairobi National Park", "Dandora", "Ruai"]


# ---------------------------------------------------------------- frame grid and static layers
def frame_grid() -> tuple[Affine, int, int]:
    """Map grid in UTM 37S covering the county, with the map's aspect ratio."""
    c = gpd.read_file(BOUNDARY).to_crs(UTM)
    x0, y0, x1, y1 = c.total_bounds
    mw, mh = int(W * MAP_BOX[2]), int(H * MAP_BOX[3])
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    res = max((x1 - x0) * 1.04 / mw, (y1 - y0) * 1.06 / mh)
    return from_bounds(cx - res * mw / 2, cy - res * mh / 2, cx + res * mw / 2, cy + res * mh / 2, mw, mh), mw, mh


def warp(path: Path, t: Affine, w: int, h: int, band=1, resampling=Resampling.bilinear, src_nodata=None) -> np.ndarray:
    with rasterio.open(path) as s:
        a = s.read(band).astype("float32")
        nd = src_nodata if src_nodata is not None else s.nodata
        if nd is not None and not np.isnan(nd):
            a[a == nd] = np.nan
        out = np.full((h, w), np.nan, dtype="float32")
        reproject(a, out, src_transform=s.transform, src_crs=s.crs, dst_transform=t, dst_crs=UTM,
                  resampling=resampling, src_nodata=np.nan, dst_nodata=np.nan)
    return out


def background(t, w, h, fade=0.40) -> np.ndarray:
    """Sentinel-2 true colour faded to about 40 % over the paper colour."""
    rgb = np.stack([warp(RASTERS / "s2_true_rgb.tif", t, w, h, band=b, resampling=Resampling.average, src_nodata=0)
                    for b in (1, 2, 3)], -1)
    paper = np.array(_rgb(PAPER), dtype="float32")
    rgb = np.where(np.isfinite(rgb), rgb, paper)
    return (fade * rgb + (1 - fade) * paper).clip(0, 255).astype("uint8")


def county_mask(t, w, h) -> np.ndarray:
    from rasterio.features import rasterize
    c = gpd.read_file(BOUNDARY).to_crs(UTM)
    return rasterize([(c.union_all(), 1)], out_shape=(h, w), transform=t, fill=0) == 1


def classify(v: np.ndarray, breaks, colours) -> np.ndarray:
    lut = np.array([_rgb(c) for c in colours], dtype="uint8")
    return lut[np.clip(np.digitize(v, breaks), 0, len(colours) - 1)]


def label_points() -> list[tuple[str, float, float]]:
    p = gpd.read_file(ROOT / "site" / "public" / "data" / "places.geojson").to_crs(UTM)
    w = gpd.read_file(WARDS).to_crs(UTM)
    out = []
    for n in LABELS:
        if n == "Embakasi":
            g = w[w["ward_name"] == "Embakasi"].representative_point()
        else:
            g = p[p["name"] == n].geometry
        if len(g):
            out.append((n, float(g.iloc[0].x), float(g.iloc[0].y)))
    return out


class Frame:
    """A matplotlib figure with the static parts drawn once; set_image() and draw() per frame."""

    def __init__(self, title: str, subtitle: str, credit: str, colourbar: dict):
        self.t, self.w, self.h = frame_grid()
        self.fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)
        self.fig.patch.set_facecolor(PAPER)
        self.ax = self.fig.add_axes(MAP_BOX)
        b = rasterio.transform.array_bounds(self.h, self.w, self.t)
        self.ext = [b[0], b[2], b[1], b[3]]   # west, east, south, north
        self.im = self.ax.imshow(np.zeros((self.h, self.w, 3), "uint8"), extent=self.ext, interpolation="nearest")
        gpd.read_file(WARDS).to_crs(UTM).boundary.plot(ax=self.ax, color="#FFFFFF", lw=0.5, alpha=0.75)
        gpd.read_file(BOUNDARY).to_crs(UTM).boundary.plot(ax=self.ax, color=INK, lw=1.4)
        for n, x, y in label_points():
            self.ax.text(x, y, n, fontsize=13, color=INK, ha="center", va="center", fontweight="semibold",
                         path_effects=[__import__("matplotlib.patheffects", fromlist=["x"]).withStroke(linewidth=3, foreground="white")])
        self.ax.set_xlim(self.ext[0], self.ext[1])
        self.ax.set_ylim(self.ext[2], self.ext[3])
        self.ax.set_axis_off()
        self.fig.text(0.015, 0.955, title, fontsize=22, fontweight="semibold", color=INK, va="center")
        self.fig.text(0.015, 0.918, subtitle, fontsize=14, color=INK2, va="center")
        self.stamp = self.fig.text(0.985, 0.952, "", fontsize=34, fontweight="semibold", color=INK, ha="right", va="center")
        self.sub_stamp = self.fig.text(0.985, 0.912, "", fontsize=15, color=INK2, ha="right", va="center")
        self.counter = self.fig.text(0.985, 0.875, "", fontsize=15, color=INK, ha="right", va="center")
        self.fig.text(0.015, 0.012, credit, fontsize=10.5, color=INK2, va="bottom", linespacing=1.35)
        self._colourbar(**colourbar)

    def _colourbar(self, colours, ticks, tick_labels, label, left_word=None, right_word=None, note=None):
        cax = self.fig.add_axes([0.30, 0.112, 0.40, 0.022])
        n = len(colours)
        cax.imshow(np.array([[_rgb(c) for c in colours]], dtype="uint8"), aspect="auto", extent=[0, n, 0, 1])
        cax.set_yticks([])
        cax.set_xticks(ticks)
        cax.set_xticklabels(tick_labels, fontsize=12, color=INK)
        cax.tick_params(length=3, color=INK2)
        for s in cax.spines.values():
            s.set_linewidth(0.5)
        self.fig.text(0.5, 0.068, label, fontsize=12.5, color=INK, ha="center")
        if left_word:
            self.fig.text(0.295, 0.123, left_word, fontsize=12, color=INK2, ha="right", va="center")
        if right_word:
            self.fig.text(0.705, 0.123, right_word, fontsize=12, color=INK2, ha="left", va="center")
        if note:
            self.fig.text(0.985, 0.123, note, fontsize=11, color=INK2, ha="right", va="center")

    def render(self, rgb: np.ndarray, stamp: str, sub: str = "", counter: str = "") -> np.ndarray:
        self.im.set_data(rgb)
        self.stamp.set_text(stamp)
        self.sub_stamp.set_text(sub)
        self.counter.set_text(counter)
        self.fig.canvas.draw()
        return np.asarray(self.fig.canvas.buffer_rgba())[..., :3].copy()


def compose(bg: np.ndarray, rgb: np.ndarray, valid: np.ndarray, alpha=0.85) -> np.ndarray:
    out = bg.astype("float32")
    out[valid] = alpha * rgb[valid] + (1 - alpha) * out[valid]
    return out.astype("uint8")


DIFF_CB = dict(colours=DIFF_COLOURS, ticks=[1, 3, 4.5, 6, 8], tick_labels=["−6", "−2", "0", "+2", "+6"],
               label="Surface temperature: difference from that morning's county median, °C",
               left_word="Cooler", right_word="Hotter")


# ---------------------------------------------------------------- writers
def write(name: str, frames: list[np.ndarray], fps: float, poster: int, hold_last_s: float = 2.0) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    MEDIA.mkdir(parents=True, exist_ok=True)
    frames = frames + [frames[-1]] * int(round(hold_last_s * fps))
    mp4, webm, gif, png = (OUT / f"{name}.{e}" for e in ("mp4", "webm", "gif", "png"))
    png = OUT / f"{name}_poster.png"
    with imageio.get_writer(mp4, fps=fps, codec="libx264", quality=8, pixelformat="yuv420p", macro_block_size=8,
                            ffmpeg_log_level="error") as wr:
        for f in frames:
            wr.append_data(f)
    try:
        with imageio.get_writer(webm, fps=fps, codec="libvpx-vp9", pixelformat="yuv420p", macro_block_size=8,
                                ffmpeg_log_level="error", output_params=["-b:v", "0", "-crf", "36"]) as wr:
            for f in frames:
                wr.append_data(f)
    except Exception as e:   # fail soft: the MP4 is the main format
        log.warning("%s.webm failed: %s", name, e)
    Image.fromarray(frames[poster]).save(png, optimize=True)
    # GIF for LinkedIn: 8 MB or less; shrink until it fits.
    for width in (1000, 800, 640, 480):
        ims = [Image.fromarray(f).resize((width, int(width * H / W)), Image.LANCZOS).quantize(colors=128, method=Image.MEDIANCUT)
               for f in frames]
        ims[0].save(gif, save_all=True, append_images=ims[1:], duration=int(1000 / fps), loop=0, optimize=True)
        if gif.stat().st_size <= 8e6:
            break
    sizes = {}
    for p in (mp4, webm, gif, png):
        if p.exists():
            shutil.copy(p, MEDIA / p.name)
            sizes[p.name] = round(p.stat().st_size / 1e6, 2)
    log.info("%s: %d frames at %s fps, sizes MB %s", name, len(frames), fps, sizes)
    return dict(frames=len(frames), fps=fps, sizes_mb=sizes, gif_width=width)


# ---------------------------------------------------------------- 1. every clear hot-season morning
def mornings() -> dict:
    cat = pd.read_csv(PROCESSED / "landsat_scene_catalogue.csv")
    cat["month"] = cat["date"].str[5:7].astype(int)
    cat["year"] = cat["date"].str[:4].astype(int)
    sel = cat[cat["usable"] & cat["month"].isin([1, 2, 3]) & cat["year"].between(2014, 2026)].sort_values("date")
    fr = Frame("Every clear hot-season morning, 2014 to 2026",
               "Land surface temperature on each clear January to March Landsat morning",
               "Data: USGS Landsat 8 and 9 Collection 2 via Microsoft Planetary Computer. Analysis: Joto Mjini Nairobi.\n" + S2_CREDIT + ".",
               DIFF_CB)
    bg = background(fr.t, fr.w, fr.h)
    cm = county_mask(fr.t, fr.w, fr.h)
    frames, dates = [], []
    for _, r in sel.iterrows():
        p = INTERIM / "landsat" / f"{r.scene_id}_lst_c.tif"
        if not p.exists():
            continue
        v = warp(p, fr.t, fr.w, fr.h)
        ok = cm & np.isfinite(v)
        if ok.sum() < 0.5 * cm.sum():
            continue
        d = v - np.nanmedian(v[ok])
        rgb = compose(bg, classify(d, DIFF_BREAKS, DIFF_COLOURS), ok)
        ts = pd.Timestamp(r.datetime_nairobi)
        frames.append(fr.render(rgb, f"{ts.day} {ts:%B %Y}", f"{ts:%H:%M} Nairobi time"))
        dates.append(r.date)
    poster = dates.index("2026-01-27") if "2026-01-27" in dates else len(frames) - 1
    info = write("hot_mornings", frames, fps=2, poster=poster)
    info.update(n_scenes=len(dates), first=dates[0], last=dates[-1])
    plt.close(fr.fig)
    return info


# ---------------------------------------------------------------- 2. Nairobi grows
def growth() -> dict:
    epochs = [1975, 1990, 2000, 2010, 2020, 2025]
    km2 = pd.read_csv(ROOT / "analysis" / "tables" / "ghsl_built_by_epoch.csv").set_index("epoch")["built_km2"]
    fr = Frame("Nairobi grows, 1975 to 2025", "Share of the ground covered by buildings, Global Human Settlement Layer",
               "Data: GHSL GHS-BUILT-S R2023A, European Commission JRC (CC BY 4.0). Analysis: Joto Mjini Nairobi.\n" + S2_CREDIT + ".",
               dict(colours=GHSL_COLOURS, ticks=[0, 1, 2, 3], tick_labels=["10 %", "30 %", "60 %", "100 %"],
                    label="Share of the ground built up (under 10 % not coloured)"))
    bg = background(fr.t, fr.w, fr.h)
    cm = county_mask(fr.t, fr.w, fr.h)
    layers = []
    for yr in epochs:
        v = warp(RASTERS / f"ghsl_built_{yr}.tif", fr.t, fr.w, fr.h)
        ok = cm & np.isfinite(v) & (v >= GHSL_BREAKS[0])
        idx = np.clip(np.digitize(v, GHSL_BREAKS) - 1, 0, 2)
        rgb = np.array([_rgb(c) for c in GHSL_COLOURS], "uint8")[idx]
        layers.append(compose(bg, rgb, ok, alpha=0.9))
    frames = []
    hold, fades = 6, 5     # at 4 fps: each epoch held 1.5 s, 5 in-between frames
    for i, yr in enumerate(epochs):
        stamp = str(yr)
        sub = "JRC projection" if yr == 2025 else ""
        cnt = f"{km2[yr]:.0f} km² built up"
        for _ in range(hold):
            frames.append(fr.render(layers[i], stamp, sub, cnt))
        if i + 1 < len(epochs):
            for k in range(1, fades + 1):
                a = k / (fades + 1)
                mix = ((1 - a) * layers[i] + a * layers[i + 1]).astype("uint8")
                j = i + 1 if a > 0.5 else i
                frames.append(fr.render(mix, str(epochs[j]), "JRC projection" if epochs[j] == 2025 else "",
                                        f"{km2[epochs[j]]:.0f} km² built up"))
    info = write("nairobi_grows", frames, fps=4, poster=len(frames) - 1)
    plt.close(fr.fig)
    return info


# ---------------------------------------------------------------- 3. a day of heat
def day() -> dict:
    """CLMS hourly LST (about 3 km) sharpened to 30 m with the same morning's Landsat scene.

    Own implementation of a Landsat residual approach (after Zlinszky 2026, Zenodo,
    doi:10.5281/zenodo.22944001; that record could not be retrieved here, so this follows the general idea
    only): for each hour h, sharpened(x) = C_h(x) + k_h * R(x), where C_h is the hourly CLMS field
    interpolated bilinearly to 30 m, R is the Landsat residual (the 30 m Landsat value minus the Landsat
    mean over the CLMS cell, interpolated the same way), and k_h scales the residual with the day's heating:
    k_h = (median C_h - median C_dawn) / (median C_overpass - median C_dawn), clipped to 0 to 1.5. Before
    sunrise fine-scale contrasts are set to near zero; at the overpass hour they equal Landsat's.
    """
    meta = json.loads(next((RAW / "clms_lst").glob("2026-*/meta.json")).read_text())
    d = meta["date"]
    cat = pd.read_csv(PROCESSED / "landsat_scene_catalogue.csv")
    sc = cat[(cat["date"] == d) & cat["usable"]].iloc[0]
    land = rasterio.open(INTERIM / "landsat" / f"{sc.scene_id}_lst_c.tif")
    L = land.read(1).astype("float32")
    lt, lcrs = land.transform, land.crs
    folder = RAW / "clms_lst" / d
    files = sorted(folder.glob("lst_*utc.tif"))
    with rasterio.open(files[0]) as s0:
        ct, ccrs, cw, ch = s0.transform, s0.crs, s0.width, s0.height

    def to_fine(a: np.ndarray) -> np.ndarray:
        out = np.full(L.shape, np.nan, "float32")
        reproject(a, out, src_transform=ct, src_crs=ccrs, dst_transform=lt, dst_crs=lcrs,
                  resampling=Resampling.bilinear, src_nodata=np.nan, dst_nodata=np.nan)
        return out

    Lc = np.full((ch, cw), np.nan, "float32")
    reproject(L, Lc, src_transform=lt, src_crs=lcrs, dst_transform=ct, dst_crs=ccrs,
              resampling=Resampling.average, src_nodata=np.nan, dst_nodata=np.nan)
    R = np.nan_to_num(L - to_fine(Lc), nan=0.0)   # where Landsat was cloudy, no fine detail is added
    hours, C = [], []
    for f in files:
        with rasterio.open(f) as s:
            a = s.read(1).astype("float32")
        hours.append(int(f.stem.split("_")[1][:2]))
        C.append(a)
    from src.rasterio_utils import county_mask as cmask_grid
    cm_fine = cmask_grid()
    meds = []
    for a in C:
        fa = to_fine(a)
        v = fa[cm_fine & np.isfinite(fa)]
        meds.append(float(np.median(v)) if v.size > 0.3 * cm_fine.sum() else np.nan)
    overpass_utc = pd.Timestamp(sc.datetime_utc).hour + pd.Timestamp(sc.datetime_utc).minute / 60
    i_ov = int(np.argmin([abs(h - overpass_utc) for h in hours]))
    i_dawn = int(np.nanargmin(meds[:4]))
    span = meds[i_ov] - meds[i_dawn]
    k = [float(np.clip((m - meds[i_dawn]) / span, 0, 1.5)) if np.isfinite(m) else np.nan for m in meds]
    # Validation at the overpass hour: Landsat averaged to the CLMS cells against CLMS itself.
    ok = np.isfinite(Lc) & np.isfinite(C[i_ov])
    diff = C[i_ov][ok] - Lc[ok]
    val = dict(n_cells=int(ok.sum()), bias_c=round(float(diff.mean()), 2), rmse_c=round(float(np.sqrt((diff ** 2).mean())), 2),
               r=round(float(np.corrcoef(C[i_ov][ok], Lc[ok])[0, 1]), 2),
               note="CLMS hour nearest the Landsat overpass minus Landsat averaged to the CLMS cells")
    fr = Frame(f"A day of heat, {pd.Timestamp(d).day} {pd.Timestamp(d):%B %Y}",
               "Land surface temperature, CLMS hourly (about 3 km), sharpened with that morning's Landsat scene",
               "Data: Copernicus Land Monitoring Service, Global Land Surface Temperature hourly v3, via the Copernicus Data Space "
               "Ecosystem; USGS Landsat 9. Analysis: Joto Mjini Nairobi.\n" + S2_CREDIT + ".",
               dict(colours=YLORBR, ticks=[1, 2, 3, 4, 5, 6], tick_labels=["20", "25", "30", "35", "40", "45"],
                    label="Land surface temperature, °C", note="No colour: cloud, no reading"))
    bg = background(fr.t, fr.w, fr.h)
    cmf = county_mask(fr.t, fr.w, fr.h)
    frames = []
    for h, a, kk in zip(hours, C, k):
        sharp = to_fine(a) + (kk if np.isfinite(kk) else 0) * R
        p = INTERIM / "_day_frame.tif"
        with rasterio.open(p, "w", driver="GTiff", width=L.shape[1], height=L.shape[0], count=1, dtype="float32",
                           crs=lcrs, transform=lt, nodata=np.nan) as dst:
            dst.write(sharp.astype("float32"), 1)
        v = warp(p, fr.t, fr.w, fr.h)
        okf = cmf & np.isfinite(v)
        rgb = compose(bg, classify(v, [20, 25, 30, 35, 40, 45], YLORBR), okf)
        local = (h + 3) % 24
        frames.append(fr.render(rgb, f"{local:02d}:00", "Nairobi time"))
    (INTERIM / "_day_frame.tif").unlink(missing_ok=True)
    i_poster = int(np.nanargmax(meds))
    info = write("day_of_heat", frames, fps=2, poster=i_poster)
    info.update(date=d, landsat_scene=sc.scene_id, hours_local=[(h + 3) % 24 for h in hours],
                county_median_c_by_hour=[round(m, 1) if np.isfinite(m) else None for m in meds],
                residual_scale_by_hour=[round(x, 2) if np.isfinite(x) else None for x in k],
                overpass_hour_local=(hours[i_ov] + 3) % 24, validation_at_overpass=val,
                method="sharpened(x) = CLMS_h(x) + k_h * Landsat residual(x); see src/animations/render.py day()")
    plt.close(fr.fig)
    return info


def main(which: list[str]) -> None:
    ex = json.loads(EXTRA.read_text()) if EXTRA.exists() else {}
    an = ex.setdefault("animations", {})
    for name, fn in (("mornings", mornings), ("growth", growth), ("day", day)):
        if which and name not in which:
            continue
        try:
            an[name] = fn()
        except Exception as e:   # fail soft per animation
            log.exception("%s failed: %s", name, e)
    EXTRA.write_text(json.dumps(ex, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])
