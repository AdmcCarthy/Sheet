# Core rules (Adam McCarthy)

Import this from a project `CLAUDE.md`. Short on purpose; detail lives in the style guide of the repo.

## Language
- British English (colour, licence noun, visualise, metre, analyse). Sentence-case headings.
- Plain words. Say what happened and why; mechanism first. "We" for our own work.
- Banned words and phrases: see `personal/banned.md` when writing prose for Adam.

## Units and numbers
- Metric first (Sm³, km, °C), boe alongside or by toggle. 1 Sm³ o.e. = 6.29 boe (Sodir convention); state it.
- 12,345.6; true minus (−); dates 20 March 2026 in prose, 2026-03-20 in data.
- No more decimals than the data supports. Every number in prose traces to data and is tested.

## Confidence
- Observed (measured or published, cited) / Derived (our calculation, method stated) / Interpreted (model or
  judgement; give range or assumption). Never hide uncertainty. Every figure: title, units, source with date,
  confidence.

## Working rules
- Act on the plan; stop at agreed gates and report outcomes plainly, including failures and skipped steps.
- Never run long or costly data fetches unasked. Never make anything public, delete data, force-push or
  commit someone's uncommitted work unasked.
- `gh repo create` may be blocked by the auto-mode classifier: prepare everything locally and hand over the
  exact commands.
- Pin dependencies between repos by tag; dependencies run one way only. Keep heavy ingestion out of the
  framework repos.
- Test the numbers you quote. Look at the rendered output before calling visual work done.
