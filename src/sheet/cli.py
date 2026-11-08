from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .frame import effective_dpi
from .layers import Overlay
from .page import SheetSpec, build_sheet, plan_layout
from .source import from_demo, from_geotiff


def _rev(p: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(p), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return "unversioned"


def load_region(relief: Path, region: str, source: str):
    out = relief / "data" / "out" / region
    meta = json.loads((out / "demo" / "meta.json").read_text())
    tif = relief / "data" / "raw" / region / "hires.tif"
    use_hires = source == "hires" or (source == "auto" and tif.exists())
    src = from_geotiff(tif, out) if use_hires else from_demo(out)
    reg = (
        {r["id"]: r for r in json.loads((relief / "regions" / "regions.json").read_text())["regions"]}
        if (relief / "regions" / "regions.json").exists()
        else {}
    )
    crs_info = reg.get(region, {}).get("crs")
    crs_name = crs_info.get("name", "Custom projection") if isinstance(crs_info, dict) else "Custom projection"
    code = meta["crs"] if str(meta["crs"]).upper().startswith("EPSG:") else ""
    attribution = list(meta.get("data", {}).get("attribution") or meta.get("attribution", []))
    if meta.get("zones", {}).get("source"):
        attribution.append(f"Climate zones: {meta['zones']['source']}")
    return src, {
        "crs": meta["crs"],
        "crs_name": f"{crs_name} ({code})" if code and code not in crs_name else crs_name,
        "attribution": attribution,
        "revision": _rev(relief),
        "zones": meta.get("zones", {}),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="sheet")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("build", "plan"):
        s = sub.add_parser(name)
        s.add_argument("region")
        s.add_argument("--relief", type=Path, default=Path("../Relief"))
        s.add_argument("--source", choices=["auto", "demo", "hires"], default="auto")
        s.add_argument("--size", default="a3-portrait")
        s.add_argument("--scale", type=float)
        s.add_argument("--dpi", type=int, default=150)
        s.add_argument("--theme", choices=["light", "dark"], default="light")
        s.add_argument("--rotation", type=float, default=0.0)
        s.add_argument("--title", default="")
        s.add_argument("--subtitle", default="")
        s.add_argument("--kicker", default="")
        s.add_argument(
            "--overlay", action="append", default=[], help="path.geojson[,name=..,stroke=..,fill=..,width=..,source=..,crs=..]"
        )
        s.add_argument("--no-graticule", action="store_true")
        s.add_argument("--format", action="append", choices=["pdf", "jpg", "tif", "png"])
        s.add_argument("--out", type=Path, default=Path("_out/sheets"))
        s.add_argument("--strict", action="store_true")
    a = p.parse_args(argv)
    src, meta = load_region(a.relief, a.region, a.source)
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
                src_crs=d.get("crs", "EPSG:4326"),
                source=d.get("source", ""),
            )
        )
    zs = [k for k, v in (meta["zones"].get("share_of_land") or {}).items() if v > 0.005 or k != "arid"] or [
        "temperate",
        "boreal",
        "tundra",
    ]
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
        zones_present=[z for z in zs if z != "arid" or (meta["zones"].get("share_of_land", {}).get("arid", 0) > 0.005)],
        graticule=not a.no_graticule,
    )
    lay = plan_layout(spec, src)
    fr = lay["frame"]
    W, H = fr.size_px
    print(
        f"{a.region}: {src.note}\n  sheet {lay['sheet']['w_mm']:.0f} x {lay['sheet']['h_mm']:.0f} mm, map frame {fr.w_mm:.0f} x {fr.h_mm:.0f} mm at 1:{int(fr.scale):,}"
        f"\n  raster {W} x {H} px = {W * H / 1e6:.0f} MP at {a.dpi} dpi; one source cell = one pixel at {effective_dpi(src.res, fr.scale):.0f} dpi"
    )
    if a.cmd == "plan":
        return 0
    m = build_sheet(spec, src, meta, a.out, tuple(a.format or ["pdf", "jpg", "tif"]))
    for f in m["files"]:
        print(f"  {f['file']}  {f['bytes'] / 1e6:.1f} MB")
    for q in m["qa"][:8]:
        print("  QA", q)
    for w in m["warnings"]:
        print("  warning:", w)
    return 1 if (a.strict and m["qa"]) else 0
