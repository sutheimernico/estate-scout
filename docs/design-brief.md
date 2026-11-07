# Design brief

**Concept.** The app is a drawing sheet (Zeichenblatt) for a property purchase: paper-grey ground, ink lines, one cadastral red, results drawn as dimensioned figures instead of dashboard cards. Every number sits on a dimension line, because the product's promise is that every number is measurable and traceable to Python.

**References and what was taken from them.**
- Title blocks and sheet conventions (ISO 7200, which replaced DIN 6771-1; ISO 5457 for sheet layout; https://www.din.de/en/getting-involved/standards-committees/natg/publications/wdc-beuth:din21:503064): hard ink rules instead of card shadows, the header as a ruled title strip, square corners (4 px), metadata in a fixed place.
- Mortgage-calculator UX reviews (https://ournethelps.com/mobile-ux-mistakes-breaking-many-mortgage-calculators/, https://indulge.digital/intelligence/articles/mortgage-calculator-ux-review): results must not hide below the fold on phones (hence the opaque result strip), live recalculation without a submit button, two-column form and result on wide screens, large touch targets, strong contrast.
- Survey conventions: Vermessungspunkt as brand mark and favicon, dimension chains with 45 degree ticks as the recurring motif.

**Type and colour.** Barlow for text and Barlow Semi Condensed for figures (the lettering of technical drawings, not an AI default); tabular lining numerals; metric-matched Arial fallback so the font swap does not move the page. Palette: paper #e7ebe6, sheet #f6f7f3, Tusche #142029, Katasterrot #c0301c for the single accent (marks, errors, the struck-out wrong figure), Flurgrün and ochre only for data. All percentages carry two decimals, all euros whole except rates.

**Signature motion (150 to 400 ms, transform and opacity only, reduced motion respected).** (1) The hero drawing draws itself line by line, dimension chain last. (2) Result figures count up from the previous value on every recalculation, and the dimension line and bars draw in. (3) On the chat intro the recorded model error, 181.210,86 instead of 181.209,86, is struck through before the number-guard verdict fades in. That case is a real recorded run, not an illustration.
