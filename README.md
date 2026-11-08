# Sheet

Static, print and plot-grade map sheets built on [Relief](https://github.com/AdmcCarthy/Relief) terrain and
[Plate](https://github.com/AdmcCarthy/Plate) page conventions. Real paper sizes (A4 to A0), a numpy terrain renderer that
streams in strips (no browser canvas limit), vector overlays and graticule, and a PDF with live text.

```
uv run sheet plan  north_sea --size a1-portrait
uv run sheet build north_sea --size a1-portrait --dpi 150 \
  --title "The North Sea basin from the sea floor up" \
  --overlay ../Wildcat/data/fields_ns.geojson,name=fields,stroke=#8a4b3c,fill=#8a4b3c33,source="Sodir (NLOD 2.0)"
```

Outputs in `_out/sheets/`: PDF, map JPEG, GeoTIFF (georeferenced), optional PNG preview, and a manifest (scale, CRS,
resolution statement, QA findings, hashes). The sheet states its scale, projection, source resolution and effective dpi.

| Option | Meaning |
|---|---|
| `--relief` | Path to a Relief checkout with print layers (default `../Relief`); Sheet asks `scripts/print_layers.py` for this frame's terrain |
| `--engine` | `layers` (default: Relief print layers) or `direct` (demo texture / `hires.tif`, flat style only) |
| `--shade`, `--contours`, `--coast` | Hillshade, generalised contours and 0 m line, all produced by Relief for the scale and dpi |
| `--size` | `a4`..`a0` with `-portrait` / `-landscape`, `slide`, `square`, `WxHmm` |
| `--scale` | Scale denominator; default the largest "nice" scale that fits the region |
| `--dpi` | Raster resolution (A0 at 300 dpi = 91 MP in about 26 s, under 1 GB) |
| `--overlay` | GeoJSON layer (repeatable): `path,name=..,stroke=..,fill=..,width=..,opacity=..,source=..,crs=..` |
| `--format` | `pdf`, `jpg`, `tif`, `png` (repeatable) |
| `--rotation` | Grid bearing of "up" on the sheet |

Portrait sheets get a three-column footer, landscape sheets a right-hand rail. See `docs/spike-a0.md` for why it is built
this way and `styleguide/sheets.md` for the furniture rules. **Terrain processing is Relief's job.** Sheet requests elevation, climate zones, hillshade and contours for one frame
(region, extent, scale, dpi) and draws what comes back (contract: Relief `docs/print-layers.md`, `layers.json`). Contour
intervals, generalisation and tile-level choice therefore stay in one place. Not yet: locator inset, grid ticks.
