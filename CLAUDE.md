# Sheet: working rules

@../../shared/idiom/CORE.md

Static map sheets for print and plotting, built from Relief terrain. Owner: Adam McCarthy. Public repo: **never copy
anything from the private Idiom repo into here** except files in its `public-manifest.txt` (see `vendor/idiom/`).

- Dependencies run one way: Sheet -> Plate (sizes, PDF stamping) and Sheet -> Relief (a sibling checkout, read only).
  Do not edit Relief from here. Plate and Relief must never import Sheet.
- Terrain processing (resampling, hillshade, contours, coast, tile levels) is Relief's: use `relief_layers.fetch`, never add it here.
- Tests find Relief at `../Relief` or `$RELIEF_DIR`; layer tests skip when Relief lacks print layers or tiles.
- Colours live in `src/sheet/style.py` and must match Relief's `preview/palette.js` (a test compares them). The numpy
  renderer is checked against a golden image from Relief's own WebGL shader (`tests/golden/`, `spikes/webgl_ref.py`).
- Memory: render in strips (`render_terrain`), never hold a full-sheet float array. Check `df` and RAM before an A0 at 300 dpi.
- Never run Relief's fetch or hires builds from here. Large outputs are not committed.
- `uv run pytest`; look at a rendered sheet (`--format png`) before calling layout work done. `styleguide/sheets.md` is the authority.
- CI fetches Relief's north_sea data from a pinned data release (`.github/workflows/ci.yml`, tag `data-2026-11-09-gebco`) so the layer, golden-image and sheet tests run instead of skipping. When Relief publishes a rebuilt north_sea, bump the tag and re-check `tests/golden/`.

