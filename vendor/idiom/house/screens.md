# Screens and map frames (public-safe)

**[Default]** Published stories are designed for a desktop screen first. A phone is checked and must work, but it does not
set the design: where the two pull apart, the screen wins, and map-heavy stories are the clearest case.

## Reference screens

| Name | Viewport (CSS px) | Used for |
|---|---|---|
| Design | 1440 × 900 | What every figure is designed and first checked on |
| Large | 1920 × 1080 | Checked for balance; nothing should look lost in it |
| Smallest | 1280 × 720 | The smallest desktop a figure may assume; text and labels must still read |
| Phone | 390 × 844 | Checked for overflow, order and legibility; secondary |

The page frame (SubScout's `ss-wrap`) is 1,152 px wide from 1,280 px up, so a full-width figure is about 1,152 px wide on every
reference screen above the smallest.

## Figures that run full width

A full-width figure is pinned with its text beneath it (SubScout `layout=full`). It may take about 60% of the viewport height, so its
drawing area is about 1,152 × 540 px on the design screen (2.1 : 1), 1,152 × 648 px on the large screen (1.8 : 1) and 1,152 × 430 px
on the smallest (2.7 : 1).

## Map frames

- **Landscape, 2 : 1.** Design a map's frame (extent) at 2 : 1 width to height, and never narrower than 16 : 9 (1.78). A frame
  at 1.44 : 1 or taller leaves a third of a full-width figure empty; a portrait frame leaves more than half.
- **Widen before cropping.** Reach 2 : 1 by adding ground east and west (more sea, more land) before cutting ground north and south,
  so the subject keeps its whole extent. Check what the new strips bring in: data that stop at the old edge leave a bare
  margin, and a margin should be context, not a hole.
- **Source images for the screen.** Render a map's base image at 2 × the page frame: at least 2,304 px on the long side for a
  2 : 1 frame. Hillshade, base colour and any raster layer share one extent, so they register without resampling.
- **Overlays stay off the subject.** A legend or key sits in the part of the frame that holds no data (open sea, a margin), or
  beside the map when the frame is wider than the map.
- **Phone.** A map frame is not redesigned for a phone. The pinned panel shows the same frame at about 36% of the viewport height,
  with the legend reduced; if that reads, it is enough.
- **Where a frame cannot be landscape** (a tall coast, a single basin), it is shown in a lane layout, or as a pair of views, and
  the reason is declared in the story.
