# Spike: A0 print rendering (2026-11-08)

**Question.** Can Sheet render terrain maps beyond what a browser canvas handles (A1 and A0 at 150-300 dpi), and which
route is best: Relief's WebGL shader in headless Chromium, tiled, or a Python-native renderer?

**Test.** North Sea, Relief `hires.tif` (150 m, 4,934 x 5,867 cells), 1:1,000,000, 741 x 881 mm map frame.

| Route | Result |
|---|---|
| **numpy strips** (Sheet) | A0 at 150 dpi, 4,376 x 5,203 px (23 MP): **5.4 s, 486 MB** peak. A0 at 300 dpi, 8,752 x 10,406 px (91 MP): **25.6 s, 899 MB** peak on a 6 GB machine. Streamed in 256-row strips into a memmap, so memory is bounded by strip size, not sheet size. |
| WebGL in headless Chromium (SwiftShader) | 10 MP full demo texture: 2.5 s wall. Works at 1:1 but the 16-bit height texture is capped at 8,192 px and canvases at 16,384 px, so A0 at 300 dpi needs tiling of both source and output. Viable, but more moving parts and no faster. |
| Chromium PDF with the A0 raster | The JPEG is passed through unchanged (1.87 MB in, 1.87 MB PDF), with live vector text on top. |

**Parity.** The numpy port of Relief's Detuned shader matches the WebGL render on a 444 x 352 px window: mean difference
0.5 / 0.46 / 0.33 levels per channel (of 255), maximum 3. This is a golden-image test (`tests/golden/`).

**Decision.** GO: raster in Python (numpy, strips), vector layers and furniture as SVG/HTML, composed and printed to PDF
by Chromium. WebGL stays Relief's interactive preview.

**Limits and next steps.**
- Source resolution, not canvas size, is now the limit: 150 m data supports about 1:640,000 at 300 dpi before it is
  interpolated. Finer print needs Relief's 25-50 m tiles (`data/out/<region>/tiles`) as a source.
- Hillshade, contours and glaciers (other Relief styles) are not ported; the house style needs none of them.
- Rotated frames work in the raster and overlays; GeoTIFF export is skipped for them.
