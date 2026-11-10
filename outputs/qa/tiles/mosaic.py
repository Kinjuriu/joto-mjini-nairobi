"""QA helper: stitch XYZ tiles into one PNG. Usage: python mosaic.py <layer> <z> <x0> <x1> <y0> <y1> <out>"""
import sys
from pathlib import Path
from PIL import Image
layer, z, x0, x1, y0, y1, out = sys.argv[1], *map(int, sys.argv[2:7]), sys.argv[7]
d = Path("site/public/tiles") / layer / str(z)
im = Image.new("RGBA", (256 * (x1 - x0 + 1), 256 * (y1 - y0 + 1)), (255, 255, 255, 255))
for i, x in enumerate(range(x0, x1 + 1)):
    for j, y in enumerate(range(y0, y1 + 1)):
        p = d / str(x) / f"{y}.webp"
        if p.exists():
            im.alpha_composite(Image.open(p).convert("RGBA"), (i * 256, j * 256))
im.convert("RGB").save(out)
