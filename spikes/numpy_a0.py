"""Spike B: North Sea terrain at A0 150 dpi (1:1,000,000), numpy strips. Prints time, peak RSS, effective dpi."""

import resource
import sys
from pathlib import Path

from PIL import Image

from sheet.frame import Frame, effective_dpi
from sheet.raster import render_terrain
from sheet.source import from_geotiff
from sheet.style import Style

relief, out = Path(sys.argv[1]), Path(sys.argv[2])
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 150
src = from_geotiff(relief / "data/raw/north_sea/hires.tif", relief / "data/out/north_sea")
x0, y0, x1, y1 = src.bounds
fr = Frame(centre=((x0 + x1) / 2, (y0 + y1) / 2), scale=1_000_000, w_mm=741, h_mm=881, dpi=dpi)
print(
    "frame px",
    fr.size_px,
    "ground km",
    [round(v / 1000) for v in fr.ground_m],
    "effective dpi (1 cell = 1 px)",
    round(effective_dpi(src.res, fr.scale)),
)
style = Style("light")
raw = out / "north_sea.npy"
info = render_terrain(src, style, fr, raw)
print(info, "peak RSS MB", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024)
import numpy as np

a = np.load(raw, mmap_mode="r")
im = Image.fromarray(np.ascontiguousarray(a))
im.save(out / "north_sea.jpg", quality=92, dpi=(dpi, dpi))
im.resize((im.width // 6, im.height // 6), Image.LANCZOS).save(out / "north_sea_thumb.png")
print(
    "jpg MB",
    round((out / "north_sea.jpg").stat().st_size / 1e6, 1),
    "peak RSS MB",
    resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024,
)
