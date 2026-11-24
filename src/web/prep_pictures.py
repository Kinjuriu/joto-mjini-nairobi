"""Prepare the two real pictures for the site (22 November 2026, D65).

Save the originals in data/raw/pictures/ first:
  landsat9.png or landsat9.jpg  NASA's Landsat 9 picture on a black background (public domain), from
                                https://science.nasa.gov/image-detail/amf-1d1315bb-91ab-4a9e-b277-5c5fc6fb6db8-2/
  classroom.jpg                 a classroom photo you have the right to use (licence and photographer noted)
Then run: uv run python -m src.web.prep_pictures

landsat9.png: the black background is made transparent, the picture is cropped to the satellite and made 240 px
wide, so it can sit small at the 10:43 line of the day chart and the school-day chart.
classroom.jpg: resized to 1200 px wide for the class-hours section of the storyboard.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "pictures"
OUT = ROOT / "site" / "public" / "figures"


def landsat() -> None:
    src = next((p for p in (RAW / "landsat9.png", RAW / "landsat9.jpg", RAW / "landsat9.jpeg") if p.exists()), None)
    if src is None:
        print("no landsat9.png or .jpg in", RAW)
        return
    im = Image.open(src).convert("RGBA")
    a = np.asarray(im).astype(float)
    # NASA's picture carries the Landsat 9 mission logo in its top-left corner; blank it so only the satellite stays.
    h, w = a.shape[:2]
    a[: int(h * 0.40), : int(w * 0.18), :3] = 0
    light = a[..., :3].max(axis=2)
    alpha = np.clip((light - 18) / 30, 0, 1) * 255          # near-black background fades to transparent
    a[..., 3] = np.minimum(a[..., 3], alpha)
    im = Image.fromarray(a.astype("uint8"), "RGBA")
    im = im.crop(im.getbbox())
    im.thumbnail((240, 240), Image.LANCZOS)
    im.save(OUT / "landsat9.png", optimize=True)
    print("wrote", OUT / "landsat9.png", im.size)


def classroom() -> None:
    src = next((p for p in (RAW / "classroom.jpg", RAW / "classroom.jpeg", RAW / "classroom.png") if p.exists()), None)
    if src is None:
        print("no classroom.jpg in", RAW)
        return
    im = Image.open(src).convert("RGB")
    im.thumbnail((1200, 1200), Image.LANCZOS)
    im.save(OUT / "classroom.jpg", quality=85, optimize=True)
    print("wrote", OUT / "classroom.jpg", im.size)


if __name__ == "__main__":
    landsat()
    classroom()
