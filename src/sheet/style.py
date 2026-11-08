"""The Relief "Detuned" house style as numbers: class breaks, climate-zone land ramps and the sea ramp.

Ported from Relief's `preview/palette.js` (ZPAL, DETUNED_SEA, tune, detunedStyle). `tests/test_style.py` compares
these constants with palette.js whenever a Relief checkout is next to this repo, so the two cannot drift silently.
"""

from __future__ import annotations

import numpy as np

LB = [0, 50, 150, 300, 600, 1000, 1500, 2000]  # land class breaks, metres
SB = [0, 20, 50, 100, 200, 500, 1000]  # sea class breaks, metres
LMAX, SMAX = 2000.0, 1300.0
ZK = ["temperate", "boreal", "tundra", "arid"]

ZPAL = {
    "light": {
        "temperate": ["#d6e8b8", "#c6dea0", "#bad38f", "#cbcf92", "#d9c897", "#ccb8a0", "#d8d0c6", "#efece8"],
        "boreal": ["#a9c7a6", "#97bb98", "#8aae8c", "#93a98b", "#a8ad96", "#ccb8a0", "#d8d0c6", "#efece8"],
        "tundra": ["#e0e3dc", "#d6dad2", "#cdd1c9", "#c6c8c0", "#c4c0b6", "#ccb8a0", "#d8d0c6", "#efece8"],
        "arid": ["#efe2c2", "#e9d6ac", "#e1c695", "#d6b382", "#c9a077", "#ccb8a0", "#d8d0c6", "#efece8"],
    },
    "dark": {
        "temperate": ["#46572f", "#4c5d33", "#536237", "#5d633b", "#665f42", "#655d50", "#85807a", "#aaa6a1"],
        "boreal": ["#2c4232", "#304836", "#354d39", "#3f513e", "#4e5547", "#655d50", "#85807a", "#aaa6a1"],
        "tundra": ["#55595a", "#585b5b", "#5b5d5c", "#5e5e5b", "#615d57", "#655d50", "#85807a", "#aaa6a1"],
        "arid": ["#5e533c", "#665a3f", "#6c5c40", "#6e5a43", "#6a5747", "#655d50", "#85807a", "#aaa6a1"],
    },
}
DETUNED_SEA = {
    "light": ["#e8f0f2", "#cfe1e6", "#aacdd8", "#7eb0c5", "#5891ae", "#3a6d94", "#264b73", "#162b50"],
    "dark": ["#3a8aa2", "#2f7690", "#25647d", "#1c526b", "#144157", "#0e3045", "#092336", "#06172a"],
}


def rgb(h: str) -> np.ndarray:
    return np.array([int(h[i : i + 2], 16) for i in (1, 3, 5)], dtype=float)


def tune(h: str, sat: float, mix: float = 0.0) -> np.ndarray:
    """Scale saturation towards the colour's own grey, then lift (mix > 0) or sink (mix < 0). Returns rounded RGB."""
    c = rgb(h)
    y = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    t = 255.0 if mix > 0 else 0.0
    g = y + (c - y) * sat
    return np.clip(np.round(g + (t - g) * abs(mix)), 0, 255)


def _stops(breaks: list[float], cols: list[np.ndarray], vmax: float) -> tuple[np.ndarray, np.ndarray]:
    t = [b / vmax for b in breaks]
    c = list(cols)
    if len(c) > len(t):
        t.append(1.0)
    return np.array(t), np.array(c)


def ramp(stops: tuple[np.ndarray, np.ndarray], t: np.ndarray) -> np.ndarray:
    """Piecewise-linear colour ramp, as Relief's 256-entry ramp texture; t in 0..1; returns float RGB 0..255."""
    ts, cs = stops
    t = np.clip(t, 0.0, 1.0)
    return np.stack([np.interp(t, ts, cs[:, k]) for k in range(3)], axis=-1)


class Style:
    """Detuned: stepped land classes cross-blended by climate zone, linear bathymetry, no shading or contours."""

    def __init__(self, theme: str = "light"):
        dark = theme == "dark"
        self.theme = theme
        self.land = {k: _stops(LB, [tune(c, 0.5, -0.08 if dark else 0.08) for c in ZPAL[theme][k]], LMAX) for k in ZK}
        self.sea = _stops(SB, [rgb(c) for c in DETUNED_SEA[theme]], SMAX)
        self.paper = np.array([250.0, 250.0, 248.0]) if not dark else np.array([20.0, 28.0, 38.0])
        edges = np.array(LB, dtype=float)
        self._mids = np.concatenate([(edges[:-1] + edges[1:]) / 2, [edges[-1] + 0.5]])

    def land_t(self, z: np.ndarray) -> np.ndarray:
        """Stepped: snap elevation to the middle of its class (Relief's bandOf), as a 0..1 ramp position."""
        i = np.clip(np.searchsorted(LB, z, side="right") - 1, 0, len(LB) - 1)
        return self._mids[i] / LMAX

    def colour(self, z: np.ndarray, zones: np.ndarray | None) -> np.ndarray:
        """RGB (uint8) for elevations `z` (metres, >0 land) with zone weights `zones` (..., 3: temperate, boreal, tundra)."""
        out = np.empty(z.shape + (3,), dtype=float)
        sea = z <= 0
        if sea.any():
            out[sea] = ramp(self.sea, -z[sea] / SMAX)
        land = ~sea
        if land.any():
            t = self.land_t(z[land])
            if zones is None:
                out[land] = ramp(self.land["temperate"], t)
            else:
                w = zones[land]
                a = np.maximum(0.0, 1.0 - w.sum(axis=-1))
                out[land] = (
                    ramp(self.land["temperate"], t) * w[:, :1]
                    + ramp(self.land["boreal"], t) * w[:, 1:2]
                    + ramp(self.land["tundra"], t) * w[:, 2:3]
                    + ramp(self.land["arid"], t) * a[:, None]
                )
        return np.clip(np.round(out), 0, 255).astype(np.uint8)
