"""Step 8: write data/processed/MANIFEST.md listing every processed file, size, grid and purpose."""
from __future__ import annotations

import rasterio

from src.config import PROCESSED, ROOT, SITE_DATA, now_local

PURPOSE = {
    "nairobi_boundary.geojson": "Nairobi County outline (geoBoundaries ADM1)",
    "nairobi_wards.geojson": "85 county assembly wards with ward_id, ward_name",
    "nairobi_places.geojson": "OSM place names, parks, forests, water, industrial areas",
    "landsat_scene_catalogue.csv": "Every Landsat 8/9 scene 2013 to now with clear fraction and county stats",
    "lst_2026_el_nino_period.csv": "Usable scenes since May 2026 (for the later El Nino phase)",
    "composites_meta.json": "Which scenes and years went into each composite",
    "nairobi_daily_air_temp.csv": "Open-Meteo ERA5 daily 2 m air temperature, Nairobi CBD grid cell, 1991 to yesterday",
    "roni.csv": "NOAA CPC Relative Oceanic Nino Index, 3-month running mean",
    "nairobi_buildings.parquet": "Overture building footprints inside the county",
    "lst_hot_season_median.tif": "Median Jan to Mar land surface temperature, deg C",
    "lst_hot_season_count.tif": "Clear observations per pixel in the hot-season composite",
    "lst_cool_season_median.tif": "Median Jun to Aug land surface temperature, deg C",
    "lst_cool_season_count.tif": "Clear observations per pixel in the cool-season composite",
    "lst_hottest_clear_day.tif": "Single usable scene with the highest county median",
    "ndvi_hot_season_median.tif": "Median NDVI of the hot-season scenes",
    "worldcover_2021.tif": "ESA WorldCover 2021 classes, 10 m, nested in the 30 m grid",
    "worldcover_majority_30m.tif": "Majority WorldCover class per 30 m cell",
    "tree_fraction_30m.tif": "Share of each 30 m cell that WorldCover calls tree cover",
    "built_fraction_30m.tif": "Share of each 30 m cell that WorldCover calls built-up",
    "grass_fraction_30m.tif": "Share of each 30 m cell that is grassland",
    "bare_fraction_30m.tif": "Share of each 30 m cell that is bare or sparse vegetation",
    "water_fraction_30m.tif": "Share of each 30 m cell that is permanent water",
    "population_100m.tif": "WorldPop 2025 constrained people per 100 m cell (native grid, EPSG:4326)",
    "population_30m.tif": "WorldPop 2025 people per 30 m cell, totals preserved",
}


def describe(p) -> str:
    if p.suffix == ".tif":
        with rasterio.open(p) as s:
            return f"{s.crs.to_string()}, {abs(s.transform.a):.0f} m" if s.crs.is_projected else f"{s.crs.to_string()}, {s.width}x{s.height}"
    return ""


def main() -> None:
    lines = ["# Processed data manifest", "", f"Generated {now_local()} (Africa/Nairobi) by `src/pipeline/manifest.py`.",
             "", "| File | Size | Grid | Purpose |", "|---|---|---|---|"]
    for base in (PROCESSED, SITE_DATA):
        for p in sorted(base.rglob("*")):
            if p.is_dir() or p.name.startswith(".") or p.name == "MANIFEST.md":
                continue
            size = p.stat().st_size
            sz = f"{size / 1e6:.1f} MB" if size > 1e5 else f"{size / 1e3:.0f} kB"
            purpose = PURPOSE.get(p.name, "")
            if p.parent.name == "lst_hot_season_by_year":
                purpose = f"Jan to Mar median land surface temperature for {p.stem}"
            if p.name.startswith("ghsl_built_"):
                purpose = f"GHSL built-up surface fraction, epoch {p.stem[-4:]}, regridded to 90 m"
            lines.append(f"| `{p.relative_to(ROOT)}` | {sz} | {describe(p)} | {purpose} |")
    (PROCESSED / "MANIFEST.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
