# Fitting Paper 3 to *Scientific Reports* — deep-dive plan

Grounded in the 5 accepted SR papers in `Other/Scientific Reports/` (applied-ML/finance:
fraud detection, temporal drift, explainable/secure detection, federated GANs) and the SR
submission guidelines.

## 0. Target spec (SR hard limits)
| Item | SR rule | Paper 3 now | Action |
|---|---|---|---|
| Title | ≤ 20 words, states the finding | 12 words | keep |
| Abstract | ≤ 200 words, **unstructured, no references** | ~99 | expand to ~180 |
| Keywords | ≤ 6 | 5 | keep / add 1 |
| Main text (Intro+Results+Discussion) | **≤ 4,500 words** | ~1,894 | grow to ~3,800–4,400 |
| Methods | **excluded from the 4,500** — can be long | none (in appendices) | build a full Methods section (~2,500–3,500) |
| References | ≤ 60 (not strict) | 18 | expand to ~45–50 |
| Display items | ≤ 8 figures+tables | 7 | keep (room for 1 more) |
| Data/Code availability | required | present (strong) | expand |
| Declarations | Competing interests, Author contributions, Funding | present | keep |

**Takeaway:** the science already clears the bar. This is *restructuring into IMRAD + a real
(uncounted) Methods section + more citations*, not bulk inflation. The 4,500-word cap on main
text means we must stay disciplined, not pad.

## 1. Target structure (from accepted SR papers)
Every accepted SR paper here uses: **Title page → Abstract → Introduction → Related work →
Methods → Results → Discussion → Conclusions & future work → Data availability → Code
availability → Declarations (Competing interests, Author contributions, Funding) → References**,
with a separate **Supplementary Information** file for overflow exhibits.

## 2. Section-by-section build (source → target, with word budget)

### Title page (new)
Author list + affiliations + corresponding author. Samir Chincholikar (Independent Researcher);
Robin Chawla (affiliation pending). Corresponding author + email.

### Abstract — ~180 words (from current 99)
Unstructured, no citations. Expand to: problem → design (pre-registered specification curve, 3
model families, 54k elicitations) → the four confirmatory findings (noise floor; determinism;
vendor monoculture; no stable resolution) → economic translation (turnover, spread, capital,
post-hoc) → real-firm decontaminated replication → one-line implication. (SR abstracts run
150–200 words; ours is currently a compressed FRL abstract.)

### Introduction — ~700 words (expand from current intro)
Keep the "reword the question, cross the IG/HY line" hook. Add: (i) why LLMs-as-credit-analysts
matters now (adoption), (ii) the elicitation-vs-confound framing, (iii) explicit contribution
bullets, (iv) a roadmap sentence. SR intros double as background — some overlap with abstract OK.

### Related work — ~700 words (NEW section)
Currently one sentence in the FRL intro. Build four short paragraphs:
1. LLM prompt-sensitivity / nondeterminism (Atil; Chon; add 3–4 CS refs on prompt robustness).
2. Specification-curve / multiverse methodology (Simonsohn, Steegen, Gelman; Camuffo).
3. LLMs in finance & credit (Hens, García-Llorente, Drinkall; add 3–4).
4. Model risk & rating economics (Cantor-Packer, Kliger-Sarig, Tang, Cornaggia; SR 11-7, Basel).
This is the single biggest citation-expansion lever (→ ~15–20 new refs).

### Results — ~2,200 words (promote appendices into full subsections)
Currently 5 compact subsections + compressed exhibits. Expand each into a full Results block
with its own figure/table and 2–4 sentences of interpretation:
- 4.1 Variance decomposition / noise floor (Table 1, keep).
- 4.2 Determinism subgrid (permutation test) — add a small figure.
- 4.3 Vendor structure (within vs cross κ) — promote to a figure (heatmap already exists as
  `fig3_provider_heatmap`).
- 4.4 Rating resolution / κ by granularity (Fig 1 IG/HY + κ figure).
- 4.5 Economic translation — turnover, Cornaggia spread, **post-hoc** capital recast + RCAP.
- 4.6 **Real-firm robustness** (currently Appendix D) — promote to a full Results subsection
  with the fingerprint-gate result and the WATCH-stratum flip-share table. This is a headline
  SR-grade contribution and should not be buried.

### Discussion — ~700 words (expand)
Implications for AI governance/model risk; why switching/pooling vendors fails; contrast with
human-agency differences of opinion; the contamination finding as a general lesson for real-firm
LLM evaluation. End with explicit **Limitations** and **Future work** paragraphs (SR expects both).

### Conclusion — ~200 words (new, short)
One tight paragraph: the prompt specification is a model-risk parameter; single-prompt ratings
are not measurements; decontaminated real-firm evidence confirms it.

### Methods — ~2,500–3,500 words (NEW, uncounted; absorb Appendices A & B and parts of D)
This is where the rigor becomes visible and SR-legible. Subsections:
- Battery construction (90 firm-quarter profiles; Altman Z″ benchmark; 15/15/15 strata).
- Specification grid (7 axes; 48-run resolution-IV fraction; seeds; effective-temperature logging).
- Models & collection (3 families, snapshots, the grok dead cell, cost, freeze/hashing).
- Parsing (A8 strict/lenient/tolerant, post-hoc).
- Statistics (Fleiss κ, Δκ, cluster bootstrap, permutation test, mixed-effects variance).
- Economic mapping (Cornaggia spread schedule; Basel CRE20 capital recast — labeled post-hoc; RCAP).
- Real-firm arm (issuer selection, per-issuer log-uniform perturbation, B2B screen, fingerprint
  gate, 12-spec × 3-seed design). Absorb Appendix D methodology here.
- Reproducibility (manifest hashes; byte-frozen corpus). SR values this.

### Data & Code availability — expand
Frozen battery, grid, response corpus, manifest hashes; the real-firm arm manifests. Point to the
archived capsule (mirror the Paper-1 Code-Ocean rigor if you archive this one too).

### Declarations — keep
Competing interests (none); Author contributions (CRediT, Robin's line pending his sign-off, no
Supervision); Funding (none); Generative-AI declaration.

### Supplementary Information — separate file
Overflow exhibits: full spec-curve panels, per-item tables, the pre-registration amendments log,
the extended real-firm arm tables, the decontamination changelog.

## 3. Concrete improvement list (the deep-dive, prioritized)
1. **Restructure FRL letter → SR IMRAD** (Related work + Methods split out). *Highest leverage.*
2. **Build the Methods section** — promote Appendices A/B/D; this is uncounted and is what
   separates an SR article from a letter. Make it the most thorough section.
3. **Promote the real-firm arm (Appendix D) to a Results subsection** — it's a genuine
   differentiator; SR reviewers will reward the decontamination gate.
4. **Expand references 18 → ~45–50** — mostly via Related work; each of the 4 threads needs
   3–5 anchor cites. Verify every DOI (no placeholders; Chon still needs a volume once in press).
5. **Grow the abstract to ~180 words**, unstructured, no citations.
6. **Add Limitations + Future work paragraphs** to the Discussion (SR expects these explicitly).
7. **Add a Conclusions & future work section.**
8. **Convert Highlights + the FRL "Data" box** into SR-native equivalents (Highlights are FRL-only;
   remove for SR — fold their content into the abstract/intro).
9. **Figures: reach 6–8 display items** — promote the determinism and vendor-heatmap exhibits from
   supplementary to main Results; keep ≤8 total; figure legends ≤350 words each.
10. **Switch class file** from `elsarticle` to SR's LaTeX template (in the SR template package;
    or Word — SR prefers Word but accepts LaTeX). Reformat references to SR (Nature) numbered style.
11. **Reporting completeness** — SR expects a self-contained Methods enabling replication; ensure
    every number in Results traces to a Methods procedure + the frozen manifest.
12. **Author affiliations + corresponding author** — resolve Robin Chawla's affiliation (still the
    one content blocker, same as the FRL version).

## 4. Word budget summary
| Block | Words | Counts toward 4,500? |
|---|---|---|
| Abstract | ~180 | no |
| Introduction | ~700 | yes |
| Related work | ~700 | yes |
| Results (6 subsections) | ~2,200 | yes |
| Discussion | ~700 | yes |
| Conclusion | ~200 | yes |
| **Main-text total** | **~4,500** | **at cap** |
| Methods | ~2,500–3,500 | no |
| References (~48) | — | no |
| Display items | 6–8 | — |

## 5. Sequence to build
1. Swap to the SR LaTeX/Word template; port title/abstract/keywords.
2. Draft Related work (citation expansion) — biggest single gain.
3. Build Methods from Appendices A/B/D + prereg.
4. Expand each Results subsection; promote the real-firm arm.
5. Expand Discussion (+ Limitations + Future work) and add Conclusion.
6. Reference audit → ~48, all DOIs verified.
7. Assemble Supplementary Information file.
8. Compile, word-count check (main ≤4,500), display-item count (≤8), abstract (≤200).

---

## 6. Folder reorganization (DONE — Paper-5 clean layout, reproducibility verified)
The repository was restructured to match Paper 5's clean convention, **non-destructively**:
- Old tree (`phaseB/00..11`, `f3/`, `src/`, `report/`, `appendixD_realarm/`, ...) moved intact to
  `_legacy/` (atomic renames; file count preserved 20,091 -> 20,091; nothing deleted).
- Clean top level: `config/ capture/ analysis/ data/{frozen,raw,panel} results/ paper/ docs/
  manifest/` + root docs (`README, LICENSE, CITATION.cff, DATA_AVAILABILITY.md,
  PREREGISTRATION*.md, reproduce.sh`).
- Analysis scripts' path constants remapped to the clean `data/` layout.
- **Verified:** `bash reproduce.sh` regenerates every `results/results_*.json`,
  `results/H1_results.json` **byte-identical** to the frozen originals, offline, no API calls.
- Disposable SEC 10-K / company-facts cache (~1.65 GB) retained under `_legacy/`; re-fetchable,
  deletable, not required for reproduction.
