from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from .frame import effective_dpi
from .layers import Overlay
from .page import SheetSpec, build_sheet, plan_layout
from .relief_layers import fetch, to_source
from .source import from_demo, from_geotiff

SEA = {"light": "#1f4468", "dark": "#a8cde0"}
LAND = {"light": "#6e5b46", "dark": "#c8b8a0"}


def _rev(p: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(p), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unversioned"


def region_meta(relief: Path, region: str) -> dict:
    """Region facts from Relief's committed files: CRS, name, extent, attribution, climate-zone source."""
    out = relief / "data" / "out" / region
    meta = json.loads((out / "demo" / "meta.json").read_text())
    regs = relief / "regions" / "regions.json"
    reg = {r["id"]: r for r in json.loads(regs.read_text())["regions"]} if regs.exists() else {}
    crs_info = reg.get(region, {}).get("crs")
    crs_name = crs_info.get("name", "Custom projection") if isinstance(crs_info, dict) else "Custom projection"
    code = meta["crs"] if str(meta["crs"]).upper().startswith("EPSG:") else ""
    attribution = list(meta.get("data", {}).get("attribution") or meta.get("attribution", []))
    if meta.get("zones", {}).get("source"):
        attribution.append(f"Climate zones: {meta['zones']['source']}")
    return {
        "crs": meta["crs"],
        "crs_name": f"{crs_name} ({code})" if code and code not in crs_name else crs_name,
        "attribution": attribution,
        "revision": _rev(relief),
        "zones": meta.get("zones", {}),
        "bounds": tuple(meta["bounds"]),
    }


def load_direct(relief: Path, region: str, source: str):
    """Fallback without Relief print layers: the committed demo texture, or hires.tif. Flat style only."""
    out = relief / "data" / "out" / region
    tif = relief / "data" / "raw" / region / "hires.tif"
    use_hires = source == "hires" or (source == "auto" and tif.exists())
    return from_geotiff(tif, out) if use_hires else from_demo(out)


def contour_overlays(lay, theme: str, dpi: int) -> tuple[list[Overlay], str]:
    f = lay.manifest["files"]["contours"]
    p = lay.path("contours")
    crs = lay.manifest["crs"]
    ov = []
    for kind, col in (("sea", SEA[theme]), ("land", LAND[theme])):
        ov.append(Overlay(p, f"contours-{kind}", col, "none", 0.09, 0.55, "", crs, "", {"kind": kind, "index": False}))
        ov.append(Overlay(p, f"contours-{kind}-index", col, "none", 0.17, 0.85, "", crs, "", {"kind": kind, "index": True}))
    note = (
        f"Contours (Relief): sea every {f['interval_sea_m']:g} m, land every {f['interval_land_m']:g} m, "
        f"heavier every {f['interval_sea_m'] * 5:g} / {f['interval_land_m'] * 5:g} m; generalised for this scale."
    )
    return ov, note


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="sheet")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("build", "plan"):
        s = sub.add_parser(name)
        s.add_argument("region")
        s.add_argument("--relief", type=Path, default=Path("../Relief"))
        s.add_argument(
            "--engine",
            choices=["layers", "direct"],
            default="layers",
            help="layers: Relief print layers (default); direct: demo texture or hires.tif, flat style only",
        )
        s.add_argument(
            "--source",
            choices=["auto", "tiles", "hires", "demo"],
            default="auto",
            help="elevation source (layers: tiles or hires; direct: demo or hires)",
        )
        s.add_argument("--size", default="a3-portrait")
        s.add_argument("--scale", type=float)
        s.add_argument("--dpi", type=int, default=150)
        s.add_argument("--theme", choices=["light", "dark"], default="light")
        s.add_argument("--rotation", type=float, default=0.0)
        s.add_argument("--title", default="")
        s.add_argument("--subtitle", default="")
        s.add_argument("--kicker", default="")
        s.add_argument("--shade", action="store_true", help="hillshade from Relief (soft, multi-directional)")
        s.add_argument("--shade-model", choices=["soft", "hard"], default="soft", help="Relief's six-light soft shade or one light at 315/45")
        s.add_argument("--contours", action="store_true", help="contour lines from Relief, generalised for the scale")
        s.add_argument("--coast", action="store_true", help="Relief's generalised 0 m line")
        s.add_argument(
            "--overlay", action="append", default=[], help="path.geojson[,name=..,stroke=..,fill=..,width=..,source=..,crs=..]"
        )
        s.add_argument("--no-graticule", action="store_true")
        s.add_argument("--extent", help="x0,y0,x1,y1 in the region CRS (metres): frame this box instead of the whole region")
        s.add_argument("--format", action="append", choices=["pdf", "jpg", "tif", "png"])
        s.add_argument("--out", type=Path, default=Path("_out/sheets"))
        s.add_argument("--strict", action="store_true")
    a = p.parse_args(argv)
    meta = region_meta(a.relief, a.region)
    if getattr(a, "extent", None):
        meta["bounds"] = tuple(float(v) for v in a.extent.split(","))
    ovs = []
    for o in a.overlay:
        path, *kv = o.split(",")
        d = dict(x.split("=", 1) for x in kv)
        ovs.append(
            Overlay(
                Path(path),
                name=d.get("name", Path(path).stem),
                stroke=d.get("stroke", "#2d3439"),
                fill=d.get("fill", "none"),
                width_mm=float(d.get("width", 0.18)),
                opacity=float(d.get("opacity", 1)),
                dash=d.get("dash", ""),
                src_crs=d.get("crs", "EPSG:4326"),
                source=d.get("source", ""),
            )
        )
    share = meta["zones"].get("share_of_land", {})
    zones = [k for k in ("temperate", "boreal", "tundra", "arid") if k != "arid" or share.get("arid", 0) > 0.005]
    spec = SheetSpec(
        region=a.region,
        title=a.title or a.region.replace("_", " ").title(),
        subtitle=a.subtitle,
        kicker=a.kicker,
        size=a.size,
        scale=a.scale,
        dpi=a.dpi,
        theme=a.theme,
        rotation=a.rotation,
        overlays=ovs,
        attribution=meta["attribution"],
        zones_present=zones,
        graticule=not a.no_graticule,
        shade=a.shade,
    )
    lay = plan_layout(spec, meta["bounds"])
    fr = lay["frame"]
    W, H = fr.size_px
    print(
        f"{a.region}: sheet {lay['sheet']['w_mm']:.0f} x {lay['sheet']['h_mm']:.0f} mm ({lay['layout']} layout), map frame {fr.w_mm:.0f} x {fr.h_mm:.0f} mm at 1:{int(fr.scale):,}"
        f"\n  raster {W} x {H} px = {W * H / 1e6:.0f} MP at {a.dpi} dpi"
    )
    if a.cmd == "plan":
        return 0
    a.out.mkdir(parents=True, exist_ok=True)
    work = tempfile.TemporaryDirectory(prefix="sheet-layers-")
    if a.engine == "layers":
        wanted = (
            ["elevation", "zones"]
            + (["hillshade"] if a.shade else [])
            + (["contours"] if a.contours else [])
            + (["coast"] if a.coast else [])
        )
        rl = fetch(a.relief, a.region, fr, Path(work.name), tuple(wanted), "tiles" if a.source in ("auto", "tiles") else "hires", a.shade_model)
        src = to_source(rl, hillshade=a.shade)
        meta["attribution"] = rl.manifest["attribution"] + [x for x in meta["attribution"] if x.startswith("Climate zones")]
        spec.attribution = meta["attribution"]
        if a.contours:
            cov, note = contour_overlays(rl, a.theme, a.dpi)
            spec.overlays = cov + spec.overlays
            spec.notes.append(note)
        if a.coast:
            spec.overlays.append(
                Overlay(
                    rl.path("coast"),
                    "coast",
                    "#2d3439" if a.theme == "light" else "#f5fdff",
                    "none",
                    0.12,
                    0.7,
                    "",
                    rl.manifest["crs"],
                )
            )
    else:
        if a.shade or a.contours or a.coast:
            raise SystemExit("--shade, --contours and --coast need --engine layers (Relief does that processing)")
        src = load_direct(a.relief, a.region, "demo" if a.source == "demo" else a.source)
    print(f"  terrain: {src.note}; one source cell = one pixel at {effective_dpi(src.res, fr.scale):.0f} dpi")
    m = build_sheet(spec, src, meta, a.out, tuple(a.format or ["pdf", "jpg", "tif"]))
    work.cleanup()
    for f in m["files"]:
        print(f"  {f['file']}  {f['bytes'] / 1e6:.1f} MB")
    for q in m["qa"][:8]:
        print("  QA", q)
    for w in m["warnings"]:
        print("  warning:", w)
    return 1 if (a.strict and m["qa"]) else 0
