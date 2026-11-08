import json
import re
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from sheet.frame import Frame, effective_dpi, fit_scale
from sheet.layers import Projector
from sheet.style import LB, SB, Style, rgb, tune

RELIEF = Path(__import__("os").environ.get("RELIEF_DIR", Path(__file__).resolve().parents[2] / "Relief"))
needs_relief = pytest.mark.skipif(
    not (RELIEF / "data/out/north_sea/demo/elev.webp").exists(), reason="no Relief checkout next to Sheet"
)


def test_frame_pixels_and_ground():
    fr = Frame(centre=(0, 0), scale=1_000_000, w_mm=100, h_mm=50, dpi=254)
    assert fr.size_px == (1000, 500)
    assert fr.m_per_px == pytest.approx(100.0)
    assert fr.ground_m == (100_000, 50_000)
    x, y = fr.ground(0, 0)
    assert (x, y) == pytest.approx((-49_950, 24_950))


def test_rotation_up_points_to_bearing():
    fr = Frame(centre=(0, 0), scale=1000, w_mm=100, h_mm=100, dpi=254, rotation=90)  # up = grid east
    top = fr.ground(500, 0)
    assert top[0] > 0 and abs(top[1]) < 1


def test_projector_roundtrip_with_rotation():
    fr = Frame(centre=(1000, 2000), scale=50_000, w_mm=200, h_mm=100, dpi=127, rotation=18)
    pr = Projector(fr, "EPSG:25832")
    gx, gy = fr.ground(300, 120)
    w, h = fr.size_px
    mx, my = pr.to_mm(gx, gy)
    assert mx == pytest.approx((300 + 0.5) / w * fr.w_mm, abs=1e-6)
    assert my == pytest.approx((120 + 0.5) / h * fr.h_mm, abs=1e-6)


def test_fit_scale_is_nice_and_fits():
    s = fit_scale((0, 0, 740_000, 880_000), 570, 761)
    assert s >= 880_000 / 0.761 and s in (1_500_000, 1_250_000, 2_000_000)
    assert effective_dpi(150, 1_000_000) == pytest.approx(169.33, abs=0.01)


def test_style_ramps_and_classes():
    st = Style("light")
    z = np.array([-5.0, -1000.0, 10.0, 49.0, 51.0, 3000.0])
    out = st.colour(z, None)
    assert out.shape == (6, 3) and out.dtype == np.uint8
    assert (out[2] == out[3]).all()  # 10 m and 49 m share the first land class
    assert not (out[3] == out[4]).all()  # 51 m is the next class
    assert tune("#d6e8b8", 1.0, 0).tolist() == rgb("#d6e8b8").tolist()


@needs_relief
def test_style_constants_match_relief_palette_js():
    js = (RELIEF / "preview/palette.js").read_text()
    lb = [int(v) for v in re.search(r"LB = \[([^\]]+)\]", js).group(1).split(",")]
    sb = [int(v) for v in re.search(r"SB = \[([^\]]+)\]", js).group(1).split(",")]
    assert lb == LB and sb == SB
    from sheet.style import DETUNED_SEA, ZPAL

    for theme in ("light", "dark"):
        zone_js = re.search(theme + r": \{(.*?)\n  \},", js, re.S).group(1)
        for zone, cols in ZPAL[theme].items():
            assert re.findall(r"#[0-9a-f]{6}", re.search(zone + r": \[([^\]]+)\]", zone_js).group(1)) == cols
    sea = re.search(r"DETUNED_SEA = \{(.*?)\};", js, re.S).group(1)
    for theme in ("light", "dark"):
        assert re.findall(r"#[0-9a-f]{6}", re.search(theme + r": \[([^\]]+)\]", sea).group(1)) == DETUNED_SEA[theme]


@needs_relief
def test_numpy_render_matches_relief_webgl_reference(tmp_path):
    """Golden image rendered once by Relief's own WebGL shader (spikes/webgl_ref.py): mean difference < 1 level."""
    from sheet.raster import render_terrain
    from sheet.source import from_demo

    src = from_demo(RELIEF / "data/out/north_sea")
    x0, y0, w, h, dpi = 1000, 1200, 444, 352, 254
    fr = Frame(
        centre=(src.left + (x0 + w / 2) * src.res, src.top - (y0 + h / 2) * src.res),
        scale=src.res * dpi * 1000 / 25.4,
        w_mm=w / dpi * 25.4,
        h_mm=h / dpi * 25.4,
        dpi=dpi,
    )
    render_terrain(src, Style("light"), fr, tmp_path / "t.npy")
    a = np.load(tmp_path / "t.npy").astype(int)
    ref = np.asarray(Image.open(Path(__file__).parent / "golden" / "north_sea_webgl.png").convert("RGB")).astype(int)
    d = np.abs(a - ref)
    assert d.mean() < 1.0 and d.max() <= 6


@needs_relief
def test_small_sheet_builds_with_clean_qa(tmp_path):
    from sheet.cli import load_direct, region_meta
    from sheet.page import SheetSpec, build_sheet

    meta = region_meta(RELIEF, "north_sea")
    src = load_direct(RELIEF, "north_sea", "demo")
    spec = SheetSpec(
        region="north_sea", title="Test sheet", kicker="TEST", size="a4-portrait", dpi=72, attribution=meta["attribution"]
    )
    m = build_sheet(spec, src, meta, tmp_path, formats=("pdf", "jpg", "tif"))
    assert not m["qa"], m["qa"]
    pdf = next(f for f in m["files"] if f["format"] == "pdf")
    from pypdf import PdfReader

    r = PdfReader(str(tmp_path / pdf["file"]))
    w, h = (float(v) / 72 * 25.4 for v in r.pages[0].mediabox[2:])
    assert (round(w), round(h)) == (210, 297)
    assert "Test sheet" in r.pages[0].extract_text()
    assert json.loads((tmp_path / (Path(pdf["file"]).stem + ".manifest.json")).read_text())["facts"]["scale"] > 0


LAYERS = (RELIEF / "scripts" / "print_layers.py").exists() and (RELIEF / "data/out/north_sea/tiles/tiles.json").exists()


@pytest.mark.skipif(not LAYERS, reason="Relief checkout without print layers or tiles")
def test_relief_layers_drive_a_shaded_contoured_sheet(tmp_path):
    """Sheet asks Relief for the frame's layers and draws them: no terrain processing happens in Sheet."""
    from sheet.cli import contour_overlays, region_meta
    from sheet.page import SheetSpec, build_sheet, plan_layout
    from sheet.relief_layers import fetch, to_source

    meta = region_meta(RELIEF, "north_sea")
    spec = SheetSpec(region="north_sea", title="Layers test", size="a4-portrait", dpi=72, scale=6_000_000, shade=True)
    fr = plan_layout(spec, meta["bounds"])["frame"]
    lay = fetch(RELIEF, "north_sea", fr, tmp_path / "layers", ("elevation", "zones", "hillshade", "contours"))
    assert lay.manifest["relief_layers"] == 1 and lay.path("contours").exists()
    src = to_source(lay, hillshade=True)
    assert src.hillshade is not None and src.hillshade.max() <= 1.6
    cov, note = contour_overlays(lay, "light", 72)
    spec.overlays, spec.notes = cov, [note]
    m = build_sheet(spec, src, meta, tmp_path, formats=("pdf",))
    assert not m["qa"], m["qa"]
    assert "Contours (Relief)" in note
