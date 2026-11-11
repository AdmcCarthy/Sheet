# Core rules (Adam McCarthy)

Import this from a project `CLAUDE.md`. Short on purpose; detail lives in Idiom `house/` and SubScout's style guide. Every item is tagged
**[Law]**, **[Default]**, **[Knowledge]** or **[Preference]** (`house/tiers.md`). Law is never bent; a Default is bent only by a declared
exception. Precedence among rules: Law, then Defaults in this file, then `house/`, then the style guide, then the repo's own
`CLAUDE.md`.

## Language
- **[Law]** British English (colour, licence noun, visualise, metre, analyse). Sentence-case headings.
- **[Law]** Impersonal voice for published work and documentation: no "we" or "I". No summary wrap-up: end on the last point.
- **[Default]** Plain words. Say what happened and why; mechanism first.
- **[Default]** Vary structure: one catchy headline, plain varied headings after it; do not give every section the same shape.
- **[Law]** No barred words or terms (`house/terms.md` and the private word list); prose is run through the checkers before it is shown.
- **[Default]** Written for executive leadership and technically trained colleagues (engineering, science): precise and measured, not academic.

## Units and numbers
- **[Default]** Metric first (Sm³, km, °C), boe alongside or by toggle. 1 Sm³ o.e. = 6.29 boe (Sodir convention); state it.
- **[Default]** 12,345.6; true minus (−); dates 20 March 2026 in prose, 2026-03-20 in data.
- **[Default]** No more decimals than the data supports. Every number in prose traces to data and is tested.

## Confidence
- **[Law]** (truth gate) Observed (measured or published, cited) / Derived (our calculation, method stated) / Interpreted (model or
  judgement; give range or assumption). Never hide uncertainty. Every figure: title, units, source with date,
  confidence.

## Reuse and licence
- **[Default]** Reuse before you build: the maintainer keeps a directory of existing repos and what each is for (Idiom `DIRECTORY.md`). Style
  comes from SubScout, map bases from Relief, facts and the knowledge store from the data engine. Say so when none fits.
- **[Law]** Datasets: look up terms and the attribution line in Idiom `DATASETS.md`, show the line wherever the data are used, and never write a licence from memory.
- **[Law]** Every public repo carries the MIT License with Acknowledgement (`house/licence.md`), and a private one from the day it, or anything
  built from it, goes public: anything built with the work says so, visibly, and never implies endorsement. Third-party data and vendored code keep their own terms.

## Working rules
- **[Preference]** Act on the plan; stop at agreed gates and report outcomes plainly, including failures and skipped steps.
- **[Law]** Never make anything public, delete data, force-push or commit someone's uncommitted work unasked.
- **[Default]** Never run long or costly data fetches unasked.
- **[Preference]** `gh repo create` may be blocked by the auto-mode classifier: prepare everything locally and hand over the
  exact commands.
- **[Default]** Pin dependencies between repos by tag; dependencies run one way only. Keep heavy ingestion out of the
  framework repos.
- **[Default]** Test the numbers you quote. Look at the rendered output before calling visual work done.
