# Map sheets

Extends the SubScout style guide (maps.md, rules.md, language.md) for printed and plotted maps. Public.

## Honesty about resolution
- Every sheet states its scale, projection, source grid size and print dpi. If the data is smoother than the print
  (more than 2x), the manifest carries a warning and the sheet says "interpolated".
- Print dpi is a choice; data resolution is a fact. At 1:1,000,000 a 150 m grid is 0.15 mm, so 169 dpi is the point where
  one cell is one pixel. Do not print finer than the data supports without saying so.

## Furniture, in named slots
- **Header:** kicker, action title, subtitle (what is shown, units, period).
- **Map frame:** thin border; graticule (dashed, muted) with labels outside the frame; the frame shrinks to the data.
- **Legend:** Relief colour bars (a stepped strip per climate zone present, then the depth bar) with units in metres.
- **Scale and north:** a true-length scale bar (round number, labelled in km), grid north (solid) and true north (line) with
  the angle between them, and the scale factor at the centre.
- **Sources:** attribution for every data source and licence, the resolution statement, date and revision.
- Portrait sheets put legend, scale and sources in a three-column footer; landscape sheets use a right-hand rail.
  Positions are fixed by the layout, so a set of sheets reads as a set. Refine slot positions here, not per sheet.

## Style
- Relief "Detuned": stepped land classes cross-blended by climate zone, linear bathymetry, no contours, no illumination.
  Land is held back, the sea floor gets the range. Colours come from `sheet.style`, tested against Relief's `palette.js`.
- Light theme for print. Type no smaller than 6 pt on paper (checked in the build).

## Static first
- Deliverables are files: PDF (vector text, embedded fonts, raster embedded as JPEG), GeoTIFF of the map raster
  (georeferenced), JPEG, PNG preview. Large files are not committed; the manifest is.
