# Appendix A — benchmark provenance (ADVISORY, POST-HOC)

**Status:** advisory artifact, post-hoc, markdown only. Modifies no frozen artifact and no
manuscript file. Provides drop-in language for Appendix A and one §2 body clause. The validation
it summarizes is the independent Altman Z″ re-execution (`03_analysis/benchmark_validation.py`,
manifest `d8ff7a26`); the pre-registration claim covers only the benchmark freeze, never this
post-hoc validation.

---

## Appendix A addition (45/45 branch — confirmed fact pattern)

> The benchmark is programmatic by construction: each item's benchmark band is the Altman Z″
> bond-rating-equivalent of its financial profile (Altman, 2005, *Emerging Markets Review* 6(4),
> 311–323; Altman & Hotchkiss, 2006, ch. 12; coefficients 6.56/3.26/6.72/1.05, cutoffs
> 2.60/1.10), with bands balanced by construction across the watch/pass/fail strata (15/15/15).
> The benchmark was frozen under pre-registration hash `b275a93c` before any model query; an
> independent post-hoc re-execution from the frozen facts alone reproduces 45/45 benchmark bands
> (validation manifest `d8ff7a26`), the tightest item lying 0.025 Z″-units from a cutoff yet
> surviving disclosed \$M rounding.

*(Word count: 88 / 120 cap.)*

---

## §2 body edit (one clause — "deterministic" licensed by construction)

Insert into the Data-and-design paragraph that introduces the credit battery (adjacent to the
constructed-item / contamination sentence):

> …constructed such that each item's benchmark band follows deterministically from its financial
> profile under the Altman Z″ bond-rating-equivalent mapping (Appendix A).

"Deterministic" is licensed here by the construction rule (a fixed Z″ mapping), not by the
recovery share; the 45/45 re-execution is reported in Appendix A as the auditable confirmation.

---

## Provenance record (for the file, not the manuscript)

- **Pinned grid (fixed from source before touching items):** Z″ = 6.56·X1 + 3.26·X2 + 6.72·X3 +
  1.05·X4 (plain Z″, no +3.25 constant); SAFE if Z″ > 2.60, DISTRESS if Z″ < 1.10, else WATCH.
  X1 = (Current assets − Current liabilities)/Total assets; X2 = Retained earnings/Total assets;
  X3 = EBIT/Total assets; X4 = book equity/Total liabilities.
- **Source:** Altman, E.I. (2005), "An emerging market credit scoring system for corporate bonds,"
  *Emerging Markets Review* 6(4), 311–323 (doi:10.1016/j.ememar.2005.09.007); Altman & Hotchkiss
  (2006), *Corporate Financial Distress and Bankruptcy*, 3rd ed., Wiley, ch. 12.
- **Result:** 45/45 exact-band, 45/45 within-one-band, zero misses. Re-executed band distribution
  15/15/15, matching the frozen benchmark. Z″ span −3.005 … 4.101; tightest cutoff margin 0.025.
- **Integrity:** `battery_90.json` hash `b275a93c…` unchanged before and after; all frozen inputs
  verified intact. New outputs only: `benchmark_validation.{json,csv,py}` → `MANIFEST_VALIDATION`
  `d8ff7a26`.

---

## Paper 2 Z″ numeric cross-check — STATUS: NOT RUN

A firm-by-firm comparison of the re-executed Z″ **values** against Paper 2's original Z″ outputs
**did not run.** The Phase 2 script compared re-executed **bands** against the frozen
`benchmark_label` only. It did not open any Paper 2 file.

- What the 45/45 already establishes: because `benchmark_label` was inherited verbatim from Paper 2's
  `data/outcomes/ground_truth.json` at battery-build time (`f3/build_battery.py`), the 45/45 band
  match already confirms consistency with Paper 2's **band labels**.
- What is still unverified: agreement at the **continuous** Z″-value level (my recomputed scalar
  Z″ vs. Paper 2's stored scalar Z″, if Paper 2 stored the numeric score). That comparison would
  require reading Paper 2 artifacts (`data/outcomes/ground_truth.json`, and any stored Z″ values),
  which are **outside** the frozen phaseB inputs.
- I did not load them, per your instruction. No API calls are involved either way — it is a local
  file read. Say the word and I will run the numeric cross-check as a separate advisory step; if
  Paper 2 stored only labels (not scalar Z″), the band-level match above is the strongest cross-check
  available and I will report that instead.
