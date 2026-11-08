"""Compose a map sheet: terrain raster + vector overlays + furniture on a physical page, printed to PDF by Chromium.

Layout "standard" (named slots, all in millimetres, scaled by `u` with the sheet size):
    header   kicker, action title, subtitle                    top
    map      frame with graticule labels outside the border    centre
    legend   climate-zone height bars and depth bar            bottom left
    scale    scale bar, grid / true north, projection facts    bottom middle
    sources  attribution, resolution statement, date           bottom right
"""

from __future__ import annotations

import datetime as dt
import functools
import hashlib
import html
import http.server
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image
from plate import sizes as psizes
from plate.render import stamp_pdf

from . import __version__
from .frame import Frame, fit_scale
from .furniture import INK, MUTED, RULE, legend_html, north_svg, projection_facts, resolution_statement, scale_bar_svg
from .layers import Overlay, Projector, graticule_svg, overlay_svg
from .raster import render_terrain
from .source import Source
from .style import Style

PT = 0.352778  # mm per point


@dataclass
class SheetSpec:
    region: str
    title: str
    subtitle: str = ""
    kicker: str = ""
    size: str = "a3-portrait"
    scale: float | None = None
    dpi: int = 150
    theme: str = "light"
    rotation: float = 0.0
    overlays: list[Overlay] = field(default_factory=list)
    attribution: list[str] = field(default_factory=list)
    zones_present: list[str] = field(default_factory=lambda: ["temperate", "boreal", "tundra"])
    graticule: bool = True
    confidence: str = "Derived"
    min_pt: float = 6.0
    layout: str = "auto"  # auto: rail for landscape sheets, standard (footer) for portrait


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def plan_layout(spec: SheetSpec, src: Source) -> dict:
    sz = psizes.parse_size(spec.size)
    W, H = sz["w_mm"], sz["h_mm"]
    u = min(2.4, max(0.9, max(W, H) / 420))
    M = 9 * u
    pad = 11 * u
    head = 21 * u
    foot = 38 * u
    layout = spec.layout if spec.layout != "auto" else ("rail" if W > H else "standard")
    fx, fy = M + pad, M + head + 5 * u
    if layout == "rail":
        railw = 0.27 * W
        fw, fh = W - 2 * M - 2 * pad - railw - 6 * u, H - M - fy - 6 * u
    else:
        railw = 0.0
        fw, fh = W - 2 * M - 2 * pad, H - M - foot - 5 * u - fy
    x0, y0, x1, y1 = src.bounds
    scale = spec.scale or fit_scale((x0, y0, x1, y1), fw, fh)
    if spec.rotation == 0:  # shrink the frame to the data and centre it in the available area
        dw, dh = (x1 - x0) / scale * 1000, (y1 - y0) / scale * 1000
        nfw, nfh = min(fw, dw), min(fh, dh)
        fx = fx + (fw - nfw) / 2  # centred across its area, top-aligned under the header
        fw, fh = nfw, nfh
    fw, fh = (
        round(fw / 25.4 * spec.dpi) / spec.dpi * 25.4,
        round(fh / 25.4 * spec.dpi) / spec.dpi * 25.4,
    )  # whole pixels: raster and ground agree
    frame = Frame(centre=((x0 + x1) / 2, (y0 + y1) / 2), scale=scale, w_mm=fw, h_mm=fh, dpi=spec.dpi, rotation=spec.rotation)
    return {
        "sheet": sz,
        "u": u,
        "M": M,
        "pad": pad,
        "head": head,
        "foot": foot,
        "fx": fx,
        "fy": fy,
        "frame": frame,
        "footer_y": fy + fh + 5 * u,
        "layout": layout,
        "railw": railw,
    }


CSS = """
@page { margin: 0; }
html, body { margin: 0; background: %(paper)s; }
.page { position: relative; overflow: hidden; background: %(paper)s; color: %(ink)s; font-family: 'Instrument Sans', system-ui, sans-serif; }
.abs { position: absolute; }
.kicker { font: 500 %(small)spt 'JetBrains Mono', monospace; letter-spacing: .08em; text-transform: uppercase; color: %(muted)s; }
.title { font: 500 %(h1)spt/1.12 'Newsreader', Georgia, serif; letter-spacing: -0.01em; margin: 0.6mm 0 0; text-wrap: balance; }
.sub { font-size: %(h2)spt; color: %(muted)s; margin: 1mm 0 0; }
.body { font-size: %(body)spt; line-height: 1.35; color: %(muted)s; }
.body b, .lg-title { color: %(ink)s; font-weight: 600; }
.lg-title { font-size: %(small)spt; margin-bottom: 1.6mm; }
.lg { font-size: %(small)spt; color: %(muted)s; width: 100%%; }
.lg-row { display: grid; grid-template-columns: 7em 1fr; align-items: center; gap: 2mm; margin-bottom: .8mm; }
.lg-steps { display: grid; grid-template-columns: repeat(var(--n), 1fr); height: 3.4mm; }
.lg-steps i { display: block; }
.lg-labs { display: grid; grid-template-columns: repeat(var(--n), 1fr); }
.lg-labs b { font-weight: 400; text-align: left; }
.lg-lin { height: 3.4mm; }
.lg-tick { position: relative; height: 3mm; }
.lg-tick b { position: absolute; font-weight: 400; transform: translateX(-50%%); }
.lg-axis { margin-bottom: 1.6mm; }
.ft text { font-family: 'Instrument Sans', sans-serif; fill: %(ink)s; }
.hr { border-top: 0.2mm solid %(rule)s; }
svg { overflow: visible; }
"""


def build_page(spec: SheetSpec, lay: dict, src: Source, style: Style, map_img: Path, meta: dict) -> tuple[str, dict]:
    sz, u, fr = lay["sheet"], lay["u"], lay["frame"]
    W, H = sz["w_mm"], sz["h_mm"]
    pr = Projector(fr, meta["crs"])
    dark = spec.theme == "dark"
    ink, muted, rule = ("#f5fdff", "#b4c7d7", "#2c3b45") if dark else (INK, MUTED, RULE)
    paper = "#{:02x}{:02x}{:02x}".format(*(int(v) for v in style.paper))
    f = {"h1": round(22 * u, 1), "h2": round(10.5 * u, 1), "body": round(7.4 * u, 1), "small": round(6.8 * u, 1)}
    css = CSS % {"paper": paper, "ink": ink, "muted": muted, "rule": rule, **f}
    fs = f["small"] * PT  # user-unit font size inside mm-based SVG
    qa_labels: list[dict] = []
    # map overlay svg: overlays and graticule clipped to the frame, labels and border outside the clip
    layers = "".join(overlay_svg(ov, pr) for ov in spec.overlays)
    gsvg, gtxt, qa_labels, gstep = ("", "", [], 0.0)
    if spec.graticule:
        gsvg, gtxt, qa_labels, gstep = graticule_svg(pr, muted, 0.12, fs)
    wmm, hmm = f"{fr.w_mm:.2f}", f"{fr.h_mm:.2f}"
    map_svg = (
        f'<svg class="abs" style="left:{lay["fx"]:.2f}mm;top:{lay["fy"]:.2f}mm" width="{wmm}mm" height="{hmm}mm" viewBox="0 0 {wmm} {hmm}">'
        f'<defs><clipPath id="mc"><rect width="{wmm}" height="{hmm}"/></clipPath></defs>'
        f'<g clip-path="url(#mc)">{layers}{gsvg}</g>'
        f'<g class="ft" style="font-size:{fs:.3f}px">{gtxt}</g>'
        f'<rect width="{wmm}" height="{hmm}" fill="none" stroke="{ink}" stroke-width="0.3"/></svg>'
    )
    # furniture blocks, placed in the footer (standard) or a right-hand rail (landscape)
    M = lay["M"]
    fy = lay["footer_y"]
    inner = W - 2 * M
    legend = legend_html(style, spec.zones_present, spec.theme)
    pf = projection_facts(fr, meta["crs"])
    bar, bw, bh = scale_bar_svg(fr, 38 * u, fs, u)
    nsvg = north_svg(fr, pf["true_north_grid_bearing"], 6.5 * u)
    res = resolution_statement(fr, src.res, src.note)
    today = dt.date.today().isoformat()
    proj_txt = (
        f"{meta.get('crs_name', meta['crs'])}. Scale factor {pf['scale_factor']:.4f} at the centre. "
        f"Grid north (GN, solid arrow) differs from true north (line) by {pf['true_north_grid_bearing']:+.1f}°. "
        f"Graticule every {gstep:g}°."
    )
    attrib = "; ".join(spec.attribution + [o.source for o in spec.overlays if o.source])
    scale_block = (
        f'<svg width="{bw + 8 * u:.2f}mm" height="{bh + 1:.2f}mm" viewBox="0 0 {bw + 8 * u:.2f} {bh + 1:.2f}" style="display:block;margin-bottom:2mm">'
        f'<g style="font-size:{fs:.3f}px">{bar}</g></svg>'
        f'<div style="display:flex;gap:3mm;align-items:flex-start"><svg width="{18 * u:.2f}mm" height="{26 * u:.2f}mm" viewBox="0 0 {18 * u:.2f} {26 * u:.2f}" style="flex:none">'
        f'<g style="font-size:{fs:.3f}px">{nsvg}</g></svg><div class="body">{html.escape(proj_txt)}</div></div>'
    )
    facts_block = (
        f'<p style="margin:0 0 1.5mm"><b>Scale</b> 1:{int(fr.scale):,} · <b>Confidence</b> {html.escape(spec.confidence)}</p>'
        f'<p style="margin:0 0 1.5mm">{html.escape(res["text"])}.</p>'
        f'<p style="margin:0 0 1.5mm"><b>Sources</b> {html.escape(attrib)}</p>'
        f'<p style="margin:0"><b>Sheet</b> {today} · {html.escape(meta.get("revision", ""))} · Sheet {__version__}</p>'
    )
    if lay["layout"] == "rail":
        rx, ry, rw = W - M - lay["railw"], lay["fy"], lay["railw"]
        furniture = (
            f'<div class="abs" style="left:{rx - 3 * u:.2f}mm;top:{ry:.2f}mm;height:{H - M - ry:.2f}mm;border-left:0.2mm solid {rule}"></div>'
            f'<div class="abs" style="left:{rx:.2f}mm;top:{ry:.2f}mm;width:{rw:.2f}mm;display:flex;flex-direction:column;gap:{6 * u:.1f}mm">'
            f'<div>{legend}</div><div>{scale_block}</div><div class="body">{facts_block}</div></div>'
        )
    else:
        col1, col2 = inner * 0.46, inner * 0.26
        col3 = inner - col1 - col2 - 8 * u
        furniture = (
            f'<div class="abs hr" style="left:{M:.2f}mm;top:{fy:.2f}mm;width:{inner:.2f}mm"></div>'
            f'<div class="abs" style="left:{M:.2f}mm;top:{fy + 3 * u:.2f}mm;width:{col1:.2f}mm">{legend}</div>'
            f'<div class="abs" style="left:{M + col1 + 4 * u:.2f}mm;top:{fy + 3 * u:.2f}mm;width:{col2:.2f}mm">{scale_block}</div>'
            f'<div class="abs body" style="left:{M + col1 + col2 + 8 * u:.2f}mm;top:{fy + 3 * u:.2f}mm;width:{col3:.2f}mm">{facts_block}</div>'
        )
    page = f"""<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><title>{html.escape(spec.title)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500&family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap">
<style>{css}</style></head><body>
<div class="page" id="page" style="width:{W}mm;height:{H}mm">
<div class="abs" style="left:{M:.2f}mm;top:{M:.2f}mm;width:{inner:.2f}mm">
  <div class="kicker">{html.escape(spec.kicker)}</div><h1 class="title">{html.escape(spec.title)}</h1>
  {f'<p class="sub">{html.escape(spec.subtitle)}</p>' if spec.subtitle else ""}</div>
<img class="abs" src="{map_img.name}" style="left:{lay["fx"]:.2f}mm;top:{lay["fy"]:.2f}mm;width:{fr.w_mm:.2f}mm;height:{fr.h_mm:.2f}mm">
{map_svg}
{furniture}
</div></body></html>"""
    facts = {
        "scale": fr.scale,
        "crs": meta["crs"],
        "resolution": res,
        "projection": pf,
        "graticule_deg": gstep,
        "date": today,
        "labels": len(qa_labels),
        "type_pt": {k: v for k, v in f.items()},
        "attribution": attrib,
    }
    return page, facts


def _serve(directory: Path):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(directory)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/"


QA_JS = """(minPt) => {
  const issues = [], page = document.getElementById('page').getBoundingClientRect();
  for (const t of document.querySelectorAll('.page *')) {
    const own = [...t.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
    if (!own) continue;
    const cs = getComputedStyle(t); let px = parseFloat(cs.fontSize);
    if (t instanceof SVGElement && t.getScreenCTM) { const m = t.getScreenCTM(); if (m) px = px * m.a; }
    const pt = px * 0.75;
    if (pt < minPt - 0.05) issues.push({ kind: 'small-text', pt: +pt.toFixed(2), text: t.textContent.trim().slice(0, 40) });
    const r = t.getBoundingClientRect();
    if (r.width && (r.right > page.right + 1 || r.left < page.left - 1 || r.bottom > page.bottom + 1 || r.top < page.top - 1))
      issues.push({ kind: 'outside-sheet', text: t.textContent.trim().slice(0, 40) });
  }
  return issues; }"""


def build_sheet(
    spec: SheetSpec, src: Source, meta: dict, out: Path, formats=("pdf", "jpg", "tif"), keep_raw: bool = False
) -> dict:
    from playwright.sync_api import sync_playwright

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    style = Style(spec.theme)
    lay = plan_layout(spec, src)
    fr = lay["frame"]
    stem = f"{spec.region}-{spec.size}-1to{int(fr.scale)}-{spec.dpi}dpi-{spec.theme}"
    raw = out / f"{stem}.npy"
    rinfo = render_terrain(src, style, fr, raw)
    a = np.load(raw, mmap_mode="r")
    jpg = out / f"{stem}-map.jpg"
    Image.MAX_IMAGE_PIXELS = None
    Image.fromarray(np.ascontiguousarray(a)).save(jpg, quality=92, dpi=(spec.dpi, spec.dpi), subsampling=0)
    files = []
    page_html, facts = build_page(spec, lay, src, style, jpg, meta)
    sz = lay["sheet"]
    qa: list[dict] = []
    if "pdf" in formats or "png" in formats:
        hp = out / f"{stem}.html"
        hp.write_text(page_html, encoding="utf-8")
        srv, url = _serve(out)
        try:
            with sync_playwright() as pw:
                b = pw.chromium.launch()
                pg = b.new_page(viewport={"width": int(psizes.mm_to_px(sz["w_mm"])), "height": int(psizes.mm_to_px(sz["h_mm"]))})
                errs: list[str] = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(f"{url}{hp.name}")
                pg.wait_for_load_state("networkidle")
                pg.evaluate("document.fonts.ready")
                qa = pg.evaluate(QA_JS, spec.min_pt)
                if "png" in formats:
                    png = out / f"{stem}.png"
                    px_w = sz["w_mm"] / 25.4 * spec.dpi * sz["h_mm"] / 25.4 * spec.dpi
                    dsf = min(spec.dpi / 96, 8.0) * min(1.0, (60e6 / px_w) ** 0.5)
                    pg2 = b.new_page(
                        viewport={"width": int(psizes.mm_to_px(sz["w_mm"])), "height": int(psizes.mm_to_px(sz["h_mm"]))},
                        device_scale_factor=dsf,
                    )
                    pg2.goto(f"{url}{hp.name}")
                    pg2.wait_for_load_state("networkidle")
                    pg2.evaluate("document.fonts.ready")
                    pg2.screenshot(path=str(png), type="png")
                    pg2.close()
                    files.append({"file": png.name, "format": "png (preview)", "bytes": png.stat().st_size, "sha256": _sha(png)})
                pdf = out / f"{stem}.pdf"
                pg.pdf(
                    path=str(pdf),
                    width=f"{sz['w_mm']}mm",
                    height=f"{sz['h_mm']}mm",
                    print_background=True,
                    margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
                )
                b.close()
        finally:
            srv.shutdown()
        stamp_pdf(
            pdf, spec.title, f"Scale 1:{int(fr.scale):,}; {meta['crs']}; confidence {spec.confidence}", f"Sheet, {spec.region}"
        )
        files.append({"file": pdf.name, "format": "pdf", "bytes": pdf.stat().st_size, "sha256": _sha(pdf)})
        hp.unlink()
    if "jpg" in formats:
        files.append(
            {
                "file": jpg.name,
                "format": "jpg (map only)",
                "px": rinfo["size_px"],
                "dpi": spec.dpi,
                "bytes": jpg.stat().st_size,
                "sha256": _sha(jpg),
            }
        )
    else:
        jpg.unlink()
    if "tif" in formats and fr.rotation == 0:
        import rasterio
        from rasterio.transform import from_origin

        tif = out / f"{stem}-map.tif"
        W, H = fr.size_px
        x0 = fr.centre[0] - W * fr.m_per_px / 2
        y1 = fr.centre[1] + H * fr.m_per_px / 2
        with rasterio.open(
            tif,
            "w",
            driver="GTiff",
            width=W,
            height=H,
            count=3,
            dtype="uint8",
            crs=meta["crs"],
            transform=from_origin(x0, y1, fr.m_per_px, fr.m_per_px),
            tiled=True,
            blockxsize=512,
            blockysize=512,
            compress="deflate",
            predictor=2,
            photometric="RGB",
        ) as dst:
            for j in range(0, H, 512):
                j1 = min(H, j + 512)
                dst.write(np.moveaxis(np.asarray(a[j:j1]), -1, 0), window=((j, j1), (0, W)))
        files.append(
            {"file": tif.name, "format": "geotiff (map only)", "px": [W, H], "bytes": tif.stat().st_size, "sha256": _sha(tif)}
        )
    del a
    if not keep_raw:
        raw.unlink()
    res = facts["resolution"]
    warnings = [
        f"data is {res['upsample']}× smoother than print resolution: interpolated"
        for _ in [0]
        if res["upsample"] > 1.15 and res["upsample"] > 2
    ]
    manifest = {
        "sheet": __version__,
        "region": spec.region,
        "title": spec.title,
        "size": sz,
        "frame_mm": [round(fr.w_mm, 1), round(fr.h_mm, 1)],
        "raster": rinfo,
        "facts": facts,
        "files": files,
        "qa": qa,
        "warnings": warnings,
        "source": src.note,
        "rendered": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"),
    }
    (out / f"{stem}.manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False, default=str))
    return manifest
