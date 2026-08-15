# Scientific Reports — submission checklist

| Requirement | Limit / rule | This manuscript | Status |
|---|---|---|---|
| Title | ≤ 20 words | 12 words | ✓ |
| Abstract | ≤ 200 words, unstructured, no citations | 185, unstructured, no cites | ✓ |
| Keywords | ≤ 6 | 6 | ✓ |
| Main text | ≤ 4,500 words (excl. Abstract, Methods, refs, legends) | ~2,000 | ✓ (under cap) |
| Methods | present, replication-enabling (uncounted) | ~1,100 words | ✓ |
| Structure | Intro → Related work → Results → Discussion → Conclusion → Methods | present | ✓ |
| Display items | ≤ 8 figures + tables | 2 figures + 3 tables = 5 | ✓ |
| Figure legends | ≤ 350 words each | short | ✓ |
| References | ≤ 60 (not strictly enforced) | 33 | ✓ |
| Data availability statement | required | present | ✓ |
| Code availability statement | required | present | ✓ |
| Author contributions (CRediT) | required | present (both authors) | ✓ |
| Competing interests | required | declared: none | ✓ |
| Funding | required | declared: none | ✓ |
| Corresponding author | designated | Robin Chawla | ✓ |
| Reproducibility | encouraged | full frozen corpus + `reproduce.sh`, byte-verified | ✓ (exceeds) |

## Files to submit
- `manuscript_sr.tex` (+ `manuscript_sr.pdf`) — main manuscript (article-class preview; reformat to
  the Springer Nature LaTeX/Word template at submission).
- `references.bib` — 33 references.
- Figures (separate files): `figure1_ighy.pdf`, `figureA_kappa.pdf`.
- `COVER_LETTER.md`.
- Supplementary Information (optional, single file): extended spec-curve panels, pre-registration
  amendments log, real-firm arm tables, decontamination changelog (available in `../../docs/`,
  `../../results/exhibits/`).

## Remaining before final submission (author actions)
- Reformat into the official Springer Nature **Scientific Reports** LaTeX or Word template (the
  content is complete; only the class/formatting changes).
- Optional: expand Results prose toward SR's typical density (main text may grow to ~3,500–4,000 while
  staying under the 4,500 cap) and add 1–2 figures (determinism subgrid; provider heatmap) from
  `results/exhibits/`.
- Confirm ORCIDs and corresponding-author details in the submission system.
- Deposited on Zenodo — DOI 10.5281/zenodo.21953935; added to Data availability, README, CITATION.cff, and the manuscript/cover letter.
