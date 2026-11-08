# Confidence: one system, two vocabularies

Readers meet three levels. The knowledge store (`ep_geoscience_analytics/knowledge/`) grades its items more finely, because it
has to say where a number came from and how far it has been tested. This file is the bridge, so a story built from store items
labels them the same way every time.

## The three reader-facing levels (SubScout, `styleguide/language.md`)

| Level | Meaning | Wording | Badge |
|---|---|---|---|
| **Observed** | Measured or published by the source | Plain statement, source named: "Sodir lists 56 licences" | filled dot |
| **Derived** | Calculated from observed data by a stated method | "Calculated from…", method named | ring |
| **Interpreted** | Depends on a model, assumption or judgement | Calibrated hedge plus the assumption or range | diamond |

Every figure and every quoted number carries one of the three. Interpreted never appears without its range or assumption.

## The knowledge-store grades, and the level each becomes

| Store grade | What it means there | Reader level | What the page must add |
|---|---|---|---|
| `exact` | exact by definition, or an official value cross-checked | Observed | nothing |
| `official` | an official value as delivered, with known limitations | Observed | the limitation, where it affects the reading |
| `verified` | a published relation tested and confirmed on the project's own data | Derived | the method and the data it was tested on |
| `published` | a relation from the literature not yet tested on the project's data | Interpreted | "published relation, untested here", with the citation |
| `contested` | a relation the project's own data do not support | Interpreted | the disagreement, stated as a finding, never resolved by choosing a side quietly |
| `inferred` | an inference or model used at or beyond its tested range | Interpreted | the range and the assumption |
| `placeholder` | an assumption that waits for data | Interpreted, and flagged | "placeholder: waits for data"; never in a headline figure or a KPI |

The store's **basis** (stated, definition, empirical, inferred, modelled, assumed) is a second axis and does not change the level;
it goes into the method sentence ("modelled from…", "assumed…").

**An expert statement from Adam** (the store's `expert statement` type) is Interpreted and is named as the project owner's
assumption, never dressed as a literature result.

## Rules that hold in both

- A derived value is never better than its weakest input (the store's `weakest` rule; the page inherits the lowest level).
- Certainty words (will, proves, certainly) do not attach to Interpreted figures.
- Where a calibrated likelihood scale is used (as the IPCC does), it is stated once in the appendix.
- The disclosure rule: a chosen baseline, window, exclusion, normalisation or classification is on the page, not only in the
  method.
- Simulated, synthetic and illustrative material is labelled on the figure, whatever its level.

## In prose

Observed: "In the 1990s 42 % of exploration wellbores found oil or gas." Derived: "Calculated from Sodir's completed-wellbore
and discovery tables, three-year centred." Interpreted: "Around half of the volume found since 2016 is likely to be developed,
on the assumption that discoveries under evaluation follow the 2000s pattern (range 40 to 60 %)." The first states, the second
shows its working, the third names what it rests on.
