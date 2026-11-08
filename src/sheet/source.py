"""Elevation and climate-zone sources from a Relief checkout."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class Source:
    """A regular elevation grid in a projected CRS plus climate-zone weights on the same extent."""

    z: np.ndarray  # (rows, cols) float32 metres, north-up
    left: float
    top: float
    res: float  # cell size, metres
    crs: str
    zones: np.ndarray | None  # (rows_z, cols_z, 3) float32 0..1 weights over the same extent
    note: str = ""
    zones_box: tuple[float, float, float, float] | None = (
        None  # left, top, width, height in metres; default: the grid's own extent
    )
    hillshade: np.ndarray | None = None  # shade multiplier (1.0 flat) from Relief, on its own grid
    hs_box: tuple[float, float, float] | None = None  # left, top, cell

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (self.left, self.top - self.z.shape[0] * self.res, self.left + self.z.shape[1] * self.res, self.top)


def _zones(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0


def from_demo(region_dir: Path) -> Source:
    """Relief's committed single-texture build: `data/out/<region>/demo/{elev.webp,zones.png,meta.json}`."""
    d = Path(region_dir) / "demo"
    meta = json.loads((d / "meta.json").read_text())
    px = np.asarray(Image.open(d / "elev.webp").convert("RGB"), dtype=np.float64)
    enc = meta["encoding"]
    z = (enc["base"] + (px[..., 0] * 256 + px[..., 1]) * enc["step"]).astype(np.float32)
    b = meta["bounds"]
    return Source(
        z, b[0], b[3], float(meta["cell"]), meta["crs"], _zones(d / "zones.png"), f"Relief demo texture, {meta['cell']} m"
    )


def from_geotiff(tif: Path, demo_dir: Path) -> Source:
    """A fine elevation GeoTIFF (Relief `data/raw/<region>/hires.tif`) with the demo texture's zone weights."""
    import rasterio

    with rasterio.open(tif) as r:
        z = r.read(1).astype(np.float32)
        nd = np.isnan(z)
        if nd.any():
            z[nd] = 0.0
        assert abs(r.res[0] - r.res[1]) < 1e-6, "non-square cells"
        return Source(
            z,
            r.bounds.left,
            r.bounds.top,
            float(r.res[0]),
            r.crs.to_string(),
            _zones(Path(demo_dir) / "demo" / "zones.png"),
            f"{tif.name}, {r.res[0]:g} m",
        )
