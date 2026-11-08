"""Cartographic furniture as SVG/HTML: scale bar, north arrows, legend, resolution and projection statements."""

from __future__ import annotations

import math

import numpy as np
from pyproj import Proj, Transformer

from .frame import Frame, effective_dpi
from .style import LB, LMAX, SMAX, Style, ramp

INK, MUTED, RULE = "#2d3439", "#596c7b", "#ccd6dd"


def nice_length_m(target_m: float) -> float:
    mag = 10 ** math.floor(math.log10(target_m))
    best = mag
    for k in (1, 2, 5, 10):
        if k * mag <= target_m * 1.25:
            best = k * mag
    return best


def scale_bar_svg(frame: Frame, target_mm: float, unit_pt_mm: float, u: float = 1.0) -> tuple[str, float, float]:
    """A true-length bar in sheet mm (ground metres / scale). Returns (svg, width_mm, height_mm)."""
    per_mm = frame.scale / 1000.0
    L = nice_length_m(target_mm * per_mm)
    w = L / per_mm
    h = 1.6
    n = 4
    while n > 1 and w / n < 12 * u:  # keep the labels apart at small scales
        n //= 2
    seg = w / n
    cells = "".join(
        f'<rect x="{i * seg:.2f}" y="{unit_pt_mm * 1.3:.2f}" width="{seg:.2f}" height="{h}" fill="{INK if i % 2 == 0 else "#fff"}" stroke="{INK}" stroke-width="0.15"/>'
        for i in range(n)
    )
    km = L / 1000
    labs = (
        "".join(
            f'<text x="{i * seg:.2f}" y="{unit_pt_mm * 1.1:.2f}" text-anchor="middle">{(km * i / n):g}</text>' for i in range(n)
        )
        + f'<text x="{w:.2f}" y="{unit_pt_mm * 1.1:.2f}" text-anchor="middle">{km:g} km</text>'
    )
    return f'<g class="ft">{labs}{cells}</g>', w, unit_pt_mm * 1.3 + h


def projection_facts(frame: Frame, crs: str) -> dict:
    """Scale factor and grid / true north relation at the frame centre."""
    to_ll = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    lon, lat = to_ll.transform(*frame.centre)
    proj = Proj(crs)
    fac = proj.get_factors(lon, lat)
    fwd = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    x0, y0 = fwd.transform(lon, lat)
    x1, y1 = fwd.transform(lon, lat + 0.01)
    tn_grid = math.degrees(math.atan2(x1 - x0, y1 - y0))  # bearing of true north in grid terms, clockwise from grid north
    return {"lon": lon, "lat": lat, "scale_factor": fac.parallel_scale, "true_north_grid_bearing": tn_grid}


def north_svg(frame: Frame, tn_grid: float, size_mm: float) -> str:
    """Grid-north arrow (solid) and true-north line (open) drawn in sheet orientation (up = bearing `rotation`)."""
    r = size_mm
    gn = -frame.rotation  # grid north relative to sheet-up, degrees clockwise
    tn = gn + tn_grid

    def arrow(a, fill):
        return (
            f'<g transform="rotate({a:.2f})"><path d="M0,{-r:.2f}L{r * 0.28:.2f},{r * 0.35:.2f}L0,{r * 0.15:.2f}L{-r * 0.28:.2f},{r * 0.35:.2f}Z" '
            f'fill="{fill}" stroke="{INK}" stroke-width="0.2"/></g>'
        )

    return (
        f'<g class="ft" transform="translate({r * 1.1:.2f},{r * 2.5:.2f})"><circle r="{r * 1.05:.2f}" fill="none" stroke="{RULE}" stroke-width="0.2"/>'
        f"{arrow(gn, INK)}"
        f'<g transform="rotate({tn:.2f})"><line x1="0" y1="{-r * 1.05:.2f}" x2="0" y2="{-r * 0.5:.2f}" stroke="{INK}" stroke-width="0.35"/></g>'
        f'<text x="0" y="{-r * 1.25:.2f}" text-anchor="middle" transform="rotate({gn:.2f})">GN</text></g>'
    )


def legend_html(style: Style, zones_present: list[str], theme: str = "light") -> str:
    """Colour bars as in Relief: a stepped strip per climate zone, then a linear depth gradient; labels in metres."""

    def hexs(c):
        return "#{:02x}{:02x}{:02x}".format(*(int(round(v)) for v in c))

    names = {"temperate": "Temperate", "boreal": "Boreal", "tundra": "Tundra", "arid": "Arid"}
    rows = []
    mids = np.concatenate([(np.array(LB[:-1]) + np.array(LB[1:])) / 2, [LB[-1] + 0.5]])
    for k in zones_present:
        cells = "".join(f'<i style="background:{hexs(ramp(style.land[k], np.array(m / LMAX)))}"></i>' for m in mids)
        rows.append(
            f'<div class="lg-row"><span>{names[k]}</span><div class="lg-steps" style="--n:{len(mids)}">{cells}</div></div>'
        )
    labs = "".join(f"<b>{v:,}{'+' if i == len(LB) - 1 else ''}</b>" for i, v in enumerate(LB))
    rows.append(f'<div class="lg-row lg-axis"><span></span><div class="lg-labs" style="--n:{len(LB)}">{labs}</div></div>')
    stops = ",".join(f"{hexs(ramp(style.sea, np.array(i / 23 * 1.0)))} {i / 23 * 100:.1f}%" for i in range(24))
    ticks = "".join(f'<b style="left:{v / SMAX * 100:.1f}%">{v:,}</b>' for v in (0, 250, 500, 1000))
    rows.append(
        f'<div class="lg-row"><span>Depth</span><div class="lg-lin" style="background:linear-gradient(90deg,{stops})"></div></div>'
    )
    rows.append(
        f'<div class="lg-row lg-axis"><span></span><div class="lg-tick">{ticks}<b style="left:100%">{int(SMAX):,}+</b></div></div>'
    )
    return (
        '<div class="lg"><div class="lg-title">Relief: stepped height classes by climate zone, m · Bathymetry: depth, m (linear)</div>'
        + "".join(rows)
        + "</div>"
    )


def resolution_statement(frame: Frame, source_res_m: float, source_note: str) -> dict:
    eff = effective_dpi(source_res_m, frame.scale)
    ratio = frame.dpi / eff
    return {
        "source_res_m": source_res_m,
        "effective_dpi": round(eff),
        "print_dpi": frame.dpi,
        "upsample": round(ratio, 2),
        "line_mm": round(source_res_m / frame.scale * 1000, 3),
        "text": f"Terrain grid {source_res_m:g} m ({source_res_m / frame.scale * 1000:.2f} mm at this scale), printed at {frame.dpi} dpi"
        + (f"; {ratio:.1f}× smoother than the data (interpolated)" if ratio > 1.15 else "; one grid cell or more per pixel"),
    }
