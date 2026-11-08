# Language

## Spelling and style

- **British English:** colour, licence (noun) / license (verb), visualise, metre, programme, analyse.
- **Sentence case** for headings and titles.
- **Plain words:** say what happened and why. Explain mechanism first ("why the oil is there").
- **Domain terms** get glossary tooltips on first use (tie-back, play, P50, PRMS, two-way time).
- First person plural for our own work: "we calculate", "we interpret".

## Units and numbers

- **Metric first**, boe alongside or via the page toggle. Oil-equivalent conversions follow the
  Norwegian convention (1 Sm³ o.e. = 6.29 boe); state the convention on the page.
- **Numbers in prose come from data** (`{{ … }}`), formatted by filters: `| pct`, `| volume`,
  `| about`, `| signed`, `| spark`.
- **Precision:** no more decimals than the data supports. Round in prose ("about 1.8 billion Sm³");
  the exact value is one tap away and in the numbers ledger.
- **British number style:** 12,345.6; true minus sign (−4.2%); units in a lighter weight; thin space
  before units in tables where supported.
- **Dates:** 20 March 2026 in prose; 2026-03-20 in data and tables.

## Confidence: Observed, Derived, Interpreted

Geoscience already separates observation from interpretation; SubScout's confidence levels use the
same words.

| Level | Meaning | Wording | Badge |
|---|---|---|---|
| **Observed** | Measured or published by the source | Plain statement: "Sodir lists 56 licences" | filled dot |
| **Derived** | Our calculation from observed data | "We calculate…", plus the method | ring |
| **Interpreted** | Depends on a model, assumption or judgement | Calibrated hedges ("likely", "around", "roughly") plus the assumption | diamond |

- Interpreted values carry their range or assumption (see [uncertainty.md](uncertainty.md)).
- Certainty words ("will", "proves", "certainly") are flagged when attached to Interpreted figures
  *(language check)*.
- Likelihood words may follow a calibrated scale (as the IPCC does): state it in the appendix if used.

## Kickers and labels

Kickers read like core-box labels: area · block or licence · round or date, in mono capitals,
e.g. `NCS · 34/7 · TFO2025`.
