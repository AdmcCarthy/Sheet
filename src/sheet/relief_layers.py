"""Ask Relief for the terrain layers of one frame. Sheet does no contouring, shading or terrain resampling itself.

Relief's `scripts/print_layers.py` writes elevation, climate zones, hillshade, contours and coast for a region, extent,
scale and dpi, with a `layers.json` manifest (contract `relief_layers: 1`, see Relief docs/print-layers.md).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .frame import Frame
from .source import Source


@dataclass
class Layers:
    dir: Path
    manifest: dict

    def path(self, name: str) -> Path | None:
        f = self.manifest["files"].get(name)
        return self.dir / f["file"] if f else None


def frame_extent(frame: Frame, margin_cells: float = 4.0, cell: float = 150.0) -> tuple[float, float, float, float]:
    xs, ys = zip(*frame.corners(), strict=True)
    m = margin_cells * cell
    return (min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m)


def fetch(relief: Path, region: str, frame: Frame, out: Path, layers=("elevation", "zones"), source: str = "auto",
          shade_model: str = "soft") -> Layers:
    """Run Relief's print_layers for this frame (Relief's own environment, run from its folder)."""
    relief, out = Path(relief).resolve(), Path(out).resolve()
    script = relief / "scripts" / "print_layers.py"
    if not script.exists():
        raise SystemExit(
            f"{relief} has no scripts/print_layers.py: use a Relief checkout with print layers (branch print-layers)"
        )
    ext = ",".join(f"{v:.1f}" for v in frame_extent(frame))
    uv = shutil.which("uv")
    cmd = [
        uv,
        "run",
        "--project",
        str(relief),
        "python",
        "scripts/print_layers.py",
        region,
        "--scale",
        str(frame.scale),
        "--dpi",
        str(frame.dpi),
        "--out",
        str(out),
        f"--extent={ext}",
        "--layers",
        ",".join(layers),
        "--source",
        source,
        "--shade-model",
        shade_model,
    ]
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}  # run in Relief's own environment
    r = subprocess.run(cmd, cwd=relief, capture_output=True, text=True, env=env)
    if r.returncode:
        raise SystemExit(f"Relief print_layers failed:\n{r.stderr[-1500:]}")
    return Layers(out, json.loads((out / "layers.json").read_text()))


def to_source(lay: Layers, hillshade: bool = False) -> Source:
    """The elevation, zones and (optional) hillshade Relief produced, as arrays for the strip renderer."""
    import rasterio

    with rasterio.open(lay.path("elevation")) as r:
        z = r.read(1).astype(np.float32)
        src = Source(
            z,
            r.bounds.left,
            r.bounds.top,
            float(r.res[0]),
            r.crs.to_string(),
            None,
            f"Relief print layers, {lay.manifest['source']['kind']} level {r.res[0]:g} m",
        )
    zp = lay.path("zones")
    if zp:
        with rasterio.open(zp) as r:
            src.zones = np.moveaxis(r.read().astype(np.float32) / 255.0, 0, -1)
            src.zones_box = (r.bounds.left, r.bounds.top, r.bounds.right - r.bounds.left, r.bounds.top - r.bounds.bottom)
    hp = lay.path("hillshade")
    if hillshade and hp:
        with rasterio.open(hp) as r:
            src.hillshade = r.read(1).astype(np.float32) / 100.0
            src.hs_box = (r.bounds.left, r.bounds.top, float(r.res[0]))
    return src
