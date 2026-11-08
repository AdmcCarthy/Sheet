# Maps

## Choropleth honesty (truth gate)

- **Normalise:** shade rates or densities, never raw counts; counts use symbols.
- **Area bias:** large regions dominate the eye. On the shelf, big Barents Sea blocks outweigh the
  dense North Sea; use an area-neutral form, or say so.
- **Declare the classification** (equal interval, quantile, natural breaks, or unclassed) in the fact
  strip: it changes the story.
- **Smooth small-sample areas** or flag them.

## Forms by job

| Form | Use for |
|---|---|
| Normalised choropleth | Rates per area |
| Value-by-confidence (value-by-alpha) | Fade areas with sparse evidence |
| Bivariate 3×3 | Two variables; sparingly, with a legend |
| Spikes / proportional symbols | Counts and volumes at points (spikes overlap less) |
| Dot density | Wells, discoveries, events |
| Tile grid | Equal weight per unit: the quadrant/block grid is a natural one |
| Cartogram | Occasional Outcrop only |

## Storytelling devices

- Camera choreography: each step sets a view (fly-to), driven by the same Read/Present engine.
- Layers revealed by step; linked map and chart; small-multiple maps.
- Space and time together: e.g. exploration moving north by decade.
- Annotation with leader lines and halos; an inset locator map.
- **Cut the map:** a section line opens a cross-section.
- Basemaps drawn from data (bathymetry, contours) in the room's palette.

## Technology

| Data | Renderer |
|---|---|
| ≲ 1k features, static | d3-geo → SVG |
| Thousands | d3-geo → Canvas |
| Pan, zoom, large layers | **MapLibre GL** with **PMTiles** on GitHub Pages (range requests verified: HTTP 206, CORS `*`) |
| 100k+ points | **deck.gl** over MapLibre (overlay mode is faster than interleaved) |

Leaflet is not used: its DOM rendering can't meet the performance budget for large layers.
Geometry is simplified and quantised at build time; projections and distances use equal-area CRSs
where sizes are compared.
