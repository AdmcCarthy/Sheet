# Licence and acknowledgement

Every repo of Adam McCarthy's carries the same licence: **MIT License with Acknowledgement** (SPDX identifier
`LicenseRef-MIT-Acknowledgement`). It is the MIT licence plus one condition: anything built with the work must say so, visibly
and in plain words, and must not imply endorsement. It is custom wording, so it is not OSI-approved; the repo says this in one
line so nobody is surprised.

- **Template:** `templates/LICENSE.tmpl`. Replace `{{YEAR}}` (year of first commit), `{{NAME}}` (the repo's name) and `{{URL}}`
  (its GitHub address). Do not reword the conditions.
- **README:** every repo ends with a "Licence and acknowledgement" section (plain heading, a few lines): the licence name, the
  exact acknowledgement line to use, and which parts carry other terms (data, vendored code).
- **`pyproject.toml`:** where a repo declares a licence, `license = { file = "LICENSE" }`; do not use the SPDX string, because older build
  backends reject it.
- **Third-party material keeps its own terms** and its own notice: source data (Sodir NLOD 2.0, Volve terms, Copernicus,
  EMODnet), vendored libraries (D3, fonts) and anything under `vendor/`. State them in the README, never relicense them.
- **Published stories** carry the acknowledgement in their README and, where the framework supports it, in the appendix
  ("Basis of analysis") next to the sources.
- **A repo that builds on another** (Wildcat on SubScout and Relief) acknowledges what it uses in its own README and appendix.
