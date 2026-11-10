"""Side-by-side images: NASA screenshot on the left, ours on the right, same height (chunk 6).
Run: uv run python outputs/qa/compare_with_nasa.py"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
N = ROOT / "reference/screenshots/nasa"
S = ROOT / "outputs/screenshots/v2"
OUT = S / "compare_with_nasa"
FONT = ImageFont.truetype(str(ROOT / "assets/fonts/SourceSans3-Semibold.ttf"), 30)
PAIRS = [
    ("05_overview_card_floating_over_landcover.png", "chunk3/04_landcover_1440.png", "landcover"),
    ("06_true_colour_satellite_chapter.png", "chunk3/01_space_1440.png", "true_colour"),
    ("07_false_colour_chapter_vegetation_green.png", "chunk3/02_trees_1440.png", "false_colour"),
    ("08_zoomed_in_with_clear_place_labels.png", "chunk3/07_centre-heat_1440.png", "zoomed_labels"),
    ("01_animated_wind_gif_beside_text.png", "chunk4/anim-mornings_1440.png", "animation_beside_text"),
    ("03_text_beside_fullbleed_landcover_map.png", "chunk4/landcover-table_1440.png", "heatmap_table"),
    ("02_chart_with_highlighted_period.png", "chunk4/air-chart_1440.png", "highlighted_chart"),
]
H = 900
for nasa, ours, name in PAIRS:
    a, b = Image.open(N / nasa).convert("RGB"), Image.open(S / ours).convert("RGB")
    a = a.resize((round(a.width * H / a.height), H))
    b = b.resize((round(b.width * H / b.height), H))
    c = Image.new("RGB", (a.width + b.width + 20, H + 50), "white")
    c.paste(a, (0, 50)); c.paste(b, (a.width + 20, 50))
    d = ImageDraw.Draw(c)
    d.text((10, 8), "NASA: " + nasa, fill="black", font=FONT)
    d.text((a.width + 30, 8), "Joto Mjini Nairobi: " + ours, fill="black", font=FONT)
    c.save(OUT / f"{name}.png", optimize=True)
    print(OUT / f"{name}.png")
