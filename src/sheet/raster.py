"""Strip-wise terrain raster: the Detuned style rendered for a Frame at print resolution, in bounded memory."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
from scipy.ndimage import map_coordinates

from .frame import Frame
from .source import Source
from .style import Style


def block_mean(a: np.ndarray, f: int) -> np.ndarray:
    h, w = (a.shape[0] // f) * f, (a.shape[1] // f) * f
    return a[:h, :w].reshape(h // f, f, w // f, f).mean(axis=(1, 3), dtype=np.float32)


def render_terrain(src: Source, style: Style, frame: Frame, out: Path, strip_rows: int = 256, paper_outside: bool = True) -> dict:
    """Write an (H, W, 3) uint8 raw raster to `out` (a numpy memmap file) and return timing and sampling facts.

    Where the frame needs coarser data than the source (more than 1.2 source cells per pixel) the source is first
    block-averaged, the equivalent of Relief's shader generalising by scale; otherwise sampling is bilinear.
    """
    t0 = time.perf_counter()
    W, H = frame.size_px
    k = frame.m_per_px / src.res
    f = max(1, round(k)) if k > 1.2 else 1
    z = block_mean(src.z, f) if f > 1 else src.z
    res = src.res * f
    mm = np.lib.format.open_memmap(out, mode="w+", dtype=np.uint8, shape=(H, W, 3))
    ncol, nrow = z.shape[1], z.shape[0]
    zl, zt, ext_w, ext_h = src.zones_box or (src.left, src.top, src.z.shape[1] * src.res, src.z.shape[0] * src.res)
    zones = src.zones
    ii = np.arange(W, dtype=np.float64)[None, :]
    for j0 in range(0, H, strip_rows):
        j1 = min(H, j0 + strip_rows)
        jj = np.arange(j0, j1, dtype=np.float64)[:, None]
        gx, gy = frame.ground(ii, jj)
        col = (gx - src.left) / res - 0.5
        row = (src.top - gy) / res - 0.5
        zz = map_coordinates(z, [row, col], order=1, mode="nearest", prefilter=False)
        zw = None
        if zones is not None:
            u = (gx - zl) / ext_w
            v = (zt - gy) / ext_h
            zr, zc = v * zones.shape[0] - 0.5, u * zones.shape[1] - 0.5
            zw = np.stack(
                [map_coordinates(zones[..., c], [zr, zc], order=1, mode="nearest", prefilter=False) for c in range(3)], axis=-1
            )
        rgb = style.colour(zz, zw)
        if src.hillshade is not None and style.shade:
            hl, ht, hc = src.hs_box
            m = map_coordinates(
                src.hillshade, [(ht - gy) / hc - 0.5, (gx - hl) / hc - 0.5], order=1, mode="nearest", prefilter=False
            )
            rgb = style.shade_rgb(rgb, m, zz)
        if paper_outside:
            outside = (col < -0.5) | (col > ncol - 0.5) | (row < -0.5) | (row > nrow - 0.5)
            rgb[outside] = style.paper.astype(np.uint8)
        mm[j0:j1] = rgb
    mm.flush()
    return {
        "size_px": [W, H],
        "m_per_px": frame.m_per_px,
        "source_cells_per_px": round(k, 3),
        "block_mean": f,
        "seconds": round(time.perf_counter() - t0, 2),
    }
