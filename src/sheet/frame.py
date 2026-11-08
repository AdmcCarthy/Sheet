"""Map frame geometry: where the map sits on the sheet and which ground it covers.

Sheet positions are in millimetres from the top-left of the sheet; ground positions are projected metres.
`rotation` is the grid bearing (degrees clockwise from grid north) of the direction that points UP on the sheet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Frame:
    centre: tuple[float, float]  # ground coordinates of the frame centre, metres
    scale: float  # scale denominator: 1:scale
    w_mm: float
    h_mm: float
    dpi: int
    rotation: float = 0.0

    @property
    def m_per_px(self) -> float:
        return self.scale * 25.4 / self.dpi / 1000.0

    @property
    def size_px(self) -> tuple[int, int]:
        return round(self.w_mm / 25.4 * self.dpi), round(self.h_mm / 25.4 * self.dpi)

    @property
    def ground_m(self) -> tuple[float, float]:
        return self.w_mm / 1000 * self.scale, self.h_mm / 1000 * self.scale

    def ground(self, i, j):
        """Ground (x, y) of output pixel centres (i = column, j = row); accepts numpy arrays."""
        w, h = self.size_px
        xl = (i + 0.5 - w / 2) * self.m_per_px
        yl = (h / 2 - (j + 0.5)) * self.m_per_px
        r = math.radians(self.rotation)
        c, s = math.cos(r), math.sin(r)
        return self.centre[0] + xl * c + yl * s, self.centre[1] - xl * s + yl * c

    def corners(self) -> list[tuple[float, float]]:
        w, h = self.size_px
        return [self.ground(-0.5, -0.5), self.ground(w - 0.5, -0.5), self.ground(w - 0.5, h - 0.5), self.ground(-0.5, h - 0.5)]


def fit_scale(extent: tuple[float, float, float, float], w_mm: float, h_mm: float, nice: bool = True) -> float:
    """Smallest scale denominator at which `extent` (x0, y0, x1, y1 in metres) fits a w x h mm frame."""
    ex, ey = extent[2] - extent[0], extent[3] - extent[1]
    s = max(ex / (w_mm / 1000), ey / (h_mm / 1000))
    if not nice:
        return s
    mag = 10 ** math.floor(math.log10(s))
    for k in (1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 7.5, 10):
        if k * mag >= s:
            return k * mag
    return 10 * mag


def effective_dpi(source_res_m: float, scale: float) -> float:
    """Print dpi at which one source cell is one device pixel: above this the data is upsampled."""
    return 25.4 * scale / (source_res_m * 1000)
