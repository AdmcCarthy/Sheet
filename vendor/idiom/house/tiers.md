# Tiers: what binds, what informs

Idiom is a store, and not everything in it is an instruction. Every rule or fact carries one of four tags, and the tag says what
an agent may do with it. Where an item has no tag, treat it as a Default.

| Tag | Meaning | If you cannot comply |
|---|---|---|
| **[Law]** | Non-negotiable. No exception, however good the reason looks. | Stop and ask. |
| **[Default]** | House style. Follow it unless an exception is declared, on the page or in the repo's `CLAUDE.md`, with the reason. | Declare the exception and go on. |
| **[Knowledge]** | A finding, fact or reference other repos may use. It carries its own confidence grade and source. It binds nobody. | Nothing to comply with: weigh it as evidence. |
| **[Preference]** | How Adam likes a session to run. Context decides. | Use judgement; say what you chose. |

## Law (the complete list)

1. **The truth gate** (SubScout `styleguide/rules.md`, section 1): zero baselines, one y-axis, area by area, source, units and
   confidence on every figure, persuasive choices disclosed.
2. **The voice**: impersonal in published work and documentation (replies to Adam may use "I"); British English with sentence-case
   headings; no barred words or terms (the house terms and the private word list); no summary wrap-up, every section and reply ends on its last point.
3. **The private/public line**: nothing from Idiom's private folders leaves Idiom; nothing is made public, deleted or
   force-pushed unasked, and nobody's uncommitted work is committed unasked.
4. **Licence and attribution**: the MIT License with Acknowledgement on every public repo, and on a private one from the day it, or
   anything built from it, goes public; the dataset attribution line wherever the data are used; never a licence written from memory.

Everything else in `CORE.md` and the style guides is a Default or a Preference until Adam says otherwise.

## Knowledge and how it becomes a rule

The knowledge store of the data engine, the dataset catalogue and the repo directory describe the world. They do not give orders. A
relation, a parameter or a dataset's terms informs any repo that uses it, at the grade it carries (`confidence.md`). It becomes a
Default or a Law **only when Adam promotes it**, and the promotion is recorded in Idiom with the date, the new tag and the reason.
Two limits apply:

- A `placeholder` or `contested` item is never promoted.
- A promoted item keeps its source and grade; if the evidence changes, the rule is reviewed, not left standing.

Demotion works the same way: Adam decides, the log records it.

## Marking

Tag items inline at the start of the line or in the heading, as **[Law]**, **[Default]**, **[Knowledge]** or **[Preference]**. A
file may hold several tiers. When a repo's `CLAUDE.md` contradicts a Law, the Law wins; when it contradicts a Default, the
repo's declared exception wins.
