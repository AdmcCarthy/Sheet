# Rules

Three layers: a **truth gate** that applies everywhere, **functional rules** that the register can
relax, and a **review checklist**. Rules marked *(build)* are checked automatically; the rest are
reviewed. Any rule except the truth gate can be bent with a **declared exception**.

## 1. The truth gate (all registers, never relaxed)

Cairo puts *truthful* first of his five qualities. One rule per failure mode in *How Charts Lie*:

| Failure mode | Rule |
|---|---|
| Poor design | Bars and areas start at zero *(build)*. Lines may use a non-zero baseline only with an exception note. One y-axis, never two; index two measures to a common base instead. Areas scale by area (√), never by radius *(build)*. Tufte's lie factor within 0.95–1.05 for bars, areas and bubbles *(build)*. |
| Dubious data | Every figure states source (with date), units and confidence *(build)*. |
| Insufficient data | Show the full period at least once before zooming in. State the denominator (per well, per licence, per km²). |
| Hidden uncertainty | Show ranges where they exist (see [uncertainty.md](uncertainty.md)). Interpreted values never appear without their range or assumption. |
| Misleading patterns | Correlation is described as association unless a mechanism is shown *(language check)*. |

**Numbers in prose are computed from data** (`{{ … }}` expressions) *(build)*. Hand-typed numbers are
listed as "untraced" in the build report; a cited external figure uses `{{ 57 | cite: source }}`.

**The disclosure rule.** Any persuasive choice that changes how a reader sees the data is visible on
the page: a chosen baseline, time window, exclusion, normalisation or classification goes in the
fact strip or notes, and in the appendix.

**Simulated or illustrative data** is labelled as such on the figure.

## 2. Functional rules (Few, Tufte, Schwabish)

- **Choose the form by the relationship** (Few): time series, ranking, part-to-whole, deviation,
  distribution, correlation, nominal comparison, plus *geographic* and *depth*. A chart block declares
  `relationship:` and gets the default form for it.
- **Action titles:** a figure title states the finding, not the topic.
- **One emphasis at a time:** one preattentive attribute, at most one or two highlighted items.
- **Data-ink:** non-data elements just visible enough to do their job (Few rule 7, Tufte).
- **Direct labels** for ≤ 4 series; a legend for ≥ 2 series; never colour alone.
- **Small multiples** share scales.
- **Tables** when exact values, lookup or mixed units matter (see [tables.md](tables.md)).
- **No pie or donut** by default (exception allowed for two- or three-part wholes).
- **3D** only when it is the right encoding (surfaces, structure, trajectories), with a one-line reason.

## 3. Colour rules

Few's nine rules (2008), mostly enforced by the palette engine and tests:

1. Keep the background consistent behind data: **never put a chart on a photograph or gradient**.
2. Enough contrast against the background *(build: APCA)*.
3. Use colour only when it serves a purpose.
4. Different colours only for different meanings.
5. Soft colours for most data; bright or dark only to highlight.
6. Sequential scales use one hue, light to dark *(build)*.
7. Non-data components just visible enough.
8. Never red against green *(build: diverging pairs)*.
9. No visual effects, except as allowed by the Outcrop register (see [registers.md](registers.md)).

SubScout additions: colour follows the entity, never its rank; identity palettes in fixed order; more
entities than slots fold into "Other" (context grey); pages use role tokens, never raw hex.

## 4. Declared exceptions

A chart or table block may bend a functional or colour rule, openly:

```yaml
exception: { rule: zero-baseline, reason: "Differences of a few percent are the story" }
```

The figure shows a small note, and the appendix lists every exception. Truth-gate rules cannot be
excepted.

## 5. Review checklist (Tufte, *Beautiful Evidence*)

Before a story is published, answer for each step:

1. **Compared with what?** Is the comparison shown, and is it the fair one?
2. **Mechanism:** is the cause or mechanism shown, not just the pattern?
3. **Multivariate:** are the variables that matter shown together?
4. **Integration:** do words, numbers and images work together on the page?
5. **Documentation:** are sources, methods and confidence visible?
6. **Content:** is the content worth the reader's time, and is it honest?
7. **Variety:** do the steps open and look different from one another? One catchy device is good; repeated, it is a habit
   (see voice.md, Variety).

Plus: does every step have one idea? Does the arc land? Is every Interpreted claim marked?
