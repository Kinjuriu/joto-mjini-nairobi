"""Step 7: Protomaps basemap extract for the Nairobi area (no API key needed at view time).

Uses the `pmtiles` CLI (brew install pmtiles). Picks the latest daily build unless --build is given.
Run: uv run python -m src.pipeline.s7_basemap [--force] [--build 20261109]
"""
from __future__ import annotations

import argparse
import subprocess

import requests

from src.config import SITE_DATA, get_logger, should_skip

log = get_logger("s7_basemap")
BBOX = "36.55,-1.52,37.22,-1.08"   # county plus margin, lon/lat
OUT = SITE_DATA / "nairobi_basemap.pmtiles"


def latest_build() -> str:
    builds = requests.get("https://build-metadata.protomaps.dev/builds.json", timeout=60).json()
    return builds[-1]["key"].replace(".pmtiles", "")


def main(force: bool = False, build: str | None = None) -> None:
    if should_skip(OUT, force):
        return
    build = build or latest_build()
    url = f"https://build.protomaps.com/{build}.pmtiles"
    log.info("Extracting %s bbox %s maxzoom 15", url, BBOX)
    subprocess.run(["pmtiles", "extract", url, str(OUT), f"--bbox={BBOX}", "--maxzoom=15"], check=True)
    log.info("Basemap saved, %.1f MB", OUT.stat().st_size / 1e6)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--build", default=None)
    a = ap.parse_args()
    main(a.force, a.build)
