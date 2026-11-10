"""Vector layers: GeoJSON reprojected into the map frame and written as SVG paths in millimetres."""

from __future__ import annotations

import functools
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import shapely
from pyproj import CRS, Transformer
from shapely.geometry import MultiPolygon, Polygon, box, shape

from .frame import Frame


@dataclass
class Overlay:
    path: Path
    name: str = ""
    stroke: str = "#2d3439"
    fill: str = "none"
    width_mm: float = 0.18
    opacity: float = 1.0
    dash: str = ""
    src_crs: str = "EPSG:4326"
    source: str = ""  # attribution line for this layer
    where: dict | None = None  # keep features whose properties equal these values


class Projector:
    """Ground (projected metres) <-> sheet millimetres within one Frame."""

    def __init__(self, frame: Frame, crs: str):
        self.f, self.crs = frame, crs
        r = math.radians(frame.rotation)
        self.c, self.s = math.cos(r), math.sin(r)
        self.k = frame.scale / 1000.0  # ground metres per sheet millimetre
        self.tol_mm = max(0.03, 0.3 * 25.4 / frame.dpi)  # path simplification: 0.3 of a print pixel

    def to_mm(self, gx, gy):
        dx, dy = gx - self.f.centre[0], gy - self.f.centre[1]
        xl, yl = dx * self.c - dy * self.s, dx * self.s + dy * self.c
        return self.f.w_mm / 2 + xl / self.k, self.f.h_mm / 2 - yl / self.k

    def frame_polygon_ground(self) -> Polygon:
        return Polygon(self.f.corners())

    def transformer(self, src_crs: str) -> Transformer:
        return Transformer.from_crs(src_crs, self.crs, always_xy=True)


def _ring_d(coords) -> str:
    pts = list(coords)
    return "M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + "Z"


def _poly_d(p: Polygon) -> str:
    return "".join(_ring_d(r.coords) for r in [p.exterior, *p.interiors])


@functools.lru_cache(maxsize=8)
def _load_cached(path: str, mtime_ns: int, size: int) -> dict:
    return json.loads(Path(path).read_text())


def _load(path: str) -> dict:
    """Parsed GeoJSON, cached per file version: a regenerated file at the same path is read again."""
    st = Path(path).stat()
    return _load_cached(path, st.st_mtime_ns, st.st_size)


def geometry_paths(ov: Overlay, pr: Projector) -> tuple[list[str], list[str]]:
    """(polygon path data, line path data) for an overlay, clipped to the frame and simplified to 0.03 mm."""
    same_crs = CRS.from_user_input(ov.src_crs) == CRS.from_user_input(pr.crs)
    tr = None if same_crs else pr.transformer(ov.src_crs)
    clip = pr.frame_polygon_ground().buffer(pr.k * 2)
    tol = pr.k * pr.tol_mm
    polys, lines = [], []
    data = _load(str(ov.path))
    feats = data["features"] if data.get("type") == "FeatureCollection" else [data]
    for ft in feats:
        if ov.where and any(ft.get("properties", {}).get(k) != v for k, v in ov.where.items()):
            continue
        g = shape(ft["geometry"] if "geometry" in ft else ft)
        if not same_crs:
            g = shapely.transform(g, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1])))
        if not g.is_valid:  # overlays from other pipelines can carry self-touching rings; GEOS refuses to clip those
            g = shapely.make_valid(g)
        if not g.intersects(clip):
            continue
        try:
            g = g.intersection(clip).simplify(tol)
        except shapely.errors.GEOSException:
            g = shapely.make_valid(g.buffer(0)).intersection(clip).simplify(tol)
        if g.is_empty:
            continue
        g = shapely.transform(g, lambda c: np.column_stack(pr.to_mm(c[:, 0], c[:, 1])))
        parts = list(g.geoms) if hasattr(g, "geoms") else [g]
        for p in parts:
            if isinstance(p, Polygon):
                polys.append(_poly_d(p))
            elif isinstance(p, MultiPolygon):
                polys.extend(_poly_d(q) for q in p.geoms)
            elif p.geom_type == "LineString":
                lines.append("M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in p.coords))
    return polys, lines


def overlay_svg(ov: Overlay, pr: Projector) -> str:
    if ov.fill.startswith("prop:") or ov.stroke.startswith("prop:"):
        return overlay_svg_by_property(ov, pr)
    polys, lines = geometry_paths(ov, pr)
    style = f'stroke="{ov.stroke}" stroke-width="{ov.width_mm}" stroke-linejoin="round" stroke-opacity="{ov.opacity}" fill-opacity="{ov.opacity}"'
    if ov.dash:
        style += f' stroke-dasharray="{ov.dash}"'
    out = []
    if polys:
        out.append(f'<path d="{"".join(polys)}" fill="{ov.fill}" fill-rule="evenodd" {style}/>')
    if lines:
        out.append(f'<path d="{"".join(lines)}" fill="none" {style}/>')
    return f'<g data-layer="{ov.name}">' + "".join(out) + "</g>"


def nice_step(deg_per_mm: float, target_mm: float = 70.0) -> float:
    """Graticule spacing (degrees) giving lines roughly `target_mm` apart."""
    want = deg_per_mm * target_mm
    for s in (0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1, 2, 5, 10, 15, 30):
        if s >= want:
            return s
    return 30


def graticule_svg(pr: Projector, stroke: str, width_mm: float, label_pt_mm: float) -> tuple[str, str, list[dict], float]:
    """Graticule lines, label text elements, label records and the step in degrees."""
    tr = Transformer.from_crs(pr.crs, "EPSG:4326", always_xy=True)
    inv = Transformer.from_crs("EPSG:4326", pr.crs, always_xy=True)
    corners = [tr.transform(*c) for c in pr.f.corners()]
    lons, lats = [c[0] for c in corners], [c[1] for c in corners]
    # extents between corners can miss bulges (polar sheets): also sample the edge midpoints and the centre
    mids = [
        tr.transform(*pr.f.ground(i, j))
        for i in (0, pr.f.size_px[0] / 2, pr.f.size_px[0])
        for j in (0, pr.f.size_px[1] / 2, pr.f.size_px[1])
    ]
    lons += [m[0] for m in mids]
    lats += [m[1] for m in mids]
    lon0, lon1, lat0, lat1 = min(lons), max(lons), min(lats), max(lats)
    deg_per_mm = (lat1 - lat0) / max(pr.f.h_mm, 1)
    step = nice_step(deg_per_mm)
    W, H = pr.f.w_mm, pr.f.h_mm
    frame_box = box(0, 0, W, H)
    paths, labels = [], []

    def fmt(v: float, pos: str, neg: str) -> str:
        a = abs(v)
        d = int(a)
        m = round((a - d) * 60)
        txt = f"{d}°" + (f"{m:02d}′" if m else "")
        return f"{txt}{pos if v >= 0 else neg}"

    def line(pts):
        xy = [pr.to_mm(*inv.transform(lo, la)) for lo, la in pts]
        return xy

    from shapely.geometry import LineString

    n0 = math.floor(lat0 / step) * step
    lat = n0
    while lat <= lat1 + 1e-9:
        pts = [(lon0 + (lon1 - lon0) * t / 120, lat) for t in range(121)]
        ls = LineString(line(pts))
        seg = ls.intersection(frame_box)
        for part in list(seg.geoms) if hasattr(seg, "geoms") else [seg]:
            if part.is_empty or part.geom_type != "LineString":
                continue
            paths.append("M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in part.coords))
            for end, side in ((part.coords[0], "l"), (part.coords[-1], "r")):
                x, y = end
                if x < 0.5 and side == "l" or x > W - 0.5 and side == "r":
                    labels.append({"x": x, "y": y, "t": fmt(lat, "N", "S"), "side": "left" if x < 1 else "right"})
        lat += step
    m0 = math.floor(lon0 / step) * step
    lon = m0
    while lon <= lon1 + 1e-9:
        pts = [(lon, lat0 + (lat1 - lat0) * t / 120) for t in range(121)]
        ls = LineString(line(pts))
        seg = ls.intersection(frame_box)
        for part in list(seg.geoms) if hasattr(seg, "geoms") else [seg]:
            if part.is_empty or part.geom_type != "LineString":
                continue
            paths.append("M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in part.coords))
            for end in (part.coords[0], part.coords[-1]):
                x, y = end
                if y < 0.5:
                    labels.append({"x": x, "y": y, "t": fmt(lon, "E", "W"), "side": "top"})
                elif y > H - 0.5:
                    labels.append({"x": x, "y": y, "t": fmt(lon, "E", "W"), "side": "bottom"})
        lon += step
    svg = f'<path d="{"".join(paths)}" fill="none" stroke="{stroke}" stroke-width="{width_mm}" stroke-dasharray="0.8 0.8"/>'
    txt = []
    off = label_pt_mm * 0.55
    for lb in labels:
        x, y, side = lb["x"], lb["y"], lb["side"]
        if side == "left":
            txt.append(f'<text x="{x - off:.2f}" y="{y + label_pt_mm * 0.35:.2f}" text-anchor="end">{lb["t"]}</text>')
        elif side == "right":
            txt.append(f'<text x="{x + off:.2f}" y="{y + label_pt_mm * 0.35:.2f}" text-anchor="start">{lb["t"]}</text>')
        elif side == "top":
            txt.append(f'<text x="{x:.2f}" y="{y - off:.2f}" text-anchor="middle">{lb["t"]}</text>')
        else:
            txt.append(f'<text x="{x:.2f}" y="{y + label_pt_mm * 1.0 + off:.2f}" text-anchor="middle">{lb["t"]}</text>')
    return svg, "".join(txt), labels, step


def overlay_svg_by_property(ov: Overlay, pr: Projector) -> str:
    """One path per distinct colour when fill or stroke is `prop:<name>`: a geological map with hundreds of colours
    stays a few hundred paths, each carrying its own fill, and the file stays small."""
    import json

    feats = json.loads(Path(ov.path).read_text(encoding="utf-8"))["features"]
    if ov.where:
        feats = [f for f in feats if all((f.get("properties") or {}).get(k) == v for k, v in ov.where.items())]
    fill_prop = ov.fill[5:] if ov.fill.startswith("prop:") else None
    stroke_prop = ov.stroke[5:] if ov.stroke.startswith("prop:") else None
    tr = pr.transformer(ov.src_crs)
    frame_poly = pr.frame_polygon_ground()
    groups: dict[tuple[str, str], tuple[list[str], list[str]]] = {}
    for f in feats:
        row = f.get("properties") or {}
        g = shape(f["geometry"]) if f.get("geometry") else None
        if g is None or g.is_empty:
            continue
        if ov.src_crs != pr.crs:
            g = shapely.transform(g, lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1])))
        if not g.is_valid:
            g = shapely.make_valid(g)
        try:
            g = g.intersection(frame_poly)
        except shapely.errors.GEOSException:
            g = shapely.make_valid(g.buffer(0)).intersection(frame_poly)
        if g.is_empty:
            continue
        g = g.simplify(pr.tol_mm * pr.k, preserve_topology=True)
        g = shapely.transform(g, lambda c: np.column_stack(pr.to_mm(c[:, 0], c[:, 1])))
        fill = str(row.get(fill_prop, "#cccccc")) if fill_prop else ov.fill
        stroke = str(row.get(stroke_prop, ov.stroke)) if stroke_prop else ov.stroke
        polys, lines = groups.setdefault((fill, stroke), ([], []))
        for part in (list(g.geoms) if hasattr(g, "geoms") else [g]):
            if isinstance(part, Polygon):
                polys.append(_poly_d(part))
            elif isinstance(part, MultiPolygon):
                polys.extend(_poly_d(q) for q in part.geoms)
            elif part.geom_type == "LineString":
                lines.append("M" + "L".join(f"{x:.2f},{y:.2f}" for x, y in part.coords))
    out = []
    for (fill, stroke), (polys, lines) in groups.items():
        style = f'stroke="{stroke}" stroke-width="{ov.width_mm}" stroke-linejoin="round" stroke-opacity="{ov.opacity}" fill-opacity="{ov.opacity}"'
        if ov.dash:
            style += f' stroke-dasharray="{ov.dash}"'
        if polys:
            out.append(f'<path d="{"".join(polys)}" fill="{fill}" fill-rule="evenodd" {style}/>')
        if lines:
            out.append(f'<path d="{"".join(lines)}" fill="none" {style}/>')
    return f'<g data-layer="{ov.name}">' + "".join(out) + "</g>"
