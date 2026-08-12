# T8 — Machine RWA Variability (Capital Recast)
### POST-HOC ADDITION to F3 Phase B ("The Garden of Forking Prompts"). Labelled; extends, never revises.

This memo recasts the already-frozen specification-dispersion result into Basel III regulatory-capital units. **No model API calls were made.** External retrieval was limited to published regulatory text and papers, under the same quote-or-exclude discipline as T6. All confirmatory numbers in `results.json` are unchanged; T8 adds a namespaced `capital.*` results file (`results_capital.json`) and a separately-hashed input (`capital_map.json`). The analysis reads only the frozen panel `02_panel/panel.parquet`.

---

## THE single number for the main text

> **The same $45B corporate book, rated by an LLM and pushed through the Basel III standardized (ECRA) risk-weight table, requires a Pillar-1 minimum of anywhere between $2.02B and $4.22B of capital depending only on how the rating request is specified — an expected gap of $0.65B, or 20.5% of the median requirement, between any two specifications.** Seed noise accounts for essentially none of this (≈0%); 71% is driven by the prompt-design axes.

---

## 1. Scope statements (load-bearing; stated on every exhibit)

- **Pillar 1 minimum only.** No capital conservation buffer, no countercyclical/G-SIB/systemic buffers, no Pillar 2.
- **8% minimum ratio.** `capital = 0.08 × RWA`.
- **ECRA base risk weights** for rated corporate exposures (CRE20.42). No CRM, no credit-conversion factors, no maturity adjustment.
- **Equal-weight, $1B on-balance-sheet drawn corporate EAD per name**, 45 names, total book $45B (value-weight run reported as robustness).
- **"Capital" = the regulatory minimum implied by the ratings the model emits.** It is NOT an economic loss estimate and NOT a claim that any bank would deploy an LLM as its rating engine.

## 2. Verifications (quote-or-exclude satisfied)

**T8.1 — Basel III ECRA corporate risk-weight table.** Retrieved from the BIS consolidated Basel Framework, **CRE20 "Standardised approach: individual exposures", para CRE20.42** and its "Risk weight table for corporate exposures" (in force 2023-01-01, published 2020-11-26). Verbatim rows:

| External rating | AAA to AA− | A+ to A− | BBB+ to BBB− | BB+ to BB− | Below BB− | Unrated |
|---|---|---|---|---|---|---|
| Base risk weight | 20% | 50% | 75% | 100% | 150% | 100% |

> "For corporate exposures of banks incorporated in jurisdictions that allow the use of external ratings for regulatory purposes, banks will assign 'base' risk weights according to [the] table." (CRE20.42)

Frozen as `00_frozen_inputs/capital_map.json`, sha256 `6a658726…` (`MANIFEST_CAPITAL.sha256`), separate from the sealed `MANIFEST_INPUTS`. **US-implementation difference (one line, BIS primary):** the US does not use this ratings-based table — Dodd-Frank §939A bars reliance on external ratings, so the US standardized approach applies a flat 100% to most corporates (65% for certain "investment grade" corporates under the 2023 US proposal); used only as a sensitivity, not the primary map.

**Ambiguity flagged:** the ECRA table has a single "Below BB−" row at 150%, so every elicitation grade from B+ through C collapses to the same 150% weight. The capital map is therefore **coarser than the 21-grade elicitation scale below BB−** — distinctions the model draws among CCC+/CCC/CCC−/CC/C are invisible to Pillar 1. This is reported alongside the dispersion, not hidden (see §3).

**T8.3 — RCAP benchmark.** Verified from the BIS press release for **BCBS 256** (05 July 2013, *RCAP — Analysis of risk-weighted assets for credit risk in the banking book*):

> "…could result in the reported capital ratios for some outlier banks varying by as much as 2 percentage points from a 10% risk-based capital ratio benchmark (or 20% in relative terms) in either direction, although the capital ratios for most banks fall within a narrower range." (BIS press release, 05 Jul 2013; >100 banks, 32 in the benchmarking exercise; IRB internal models.)

Behn, Haselmann & Vig (JF 2022) and Mariathasan & Merrouche (JFI 2014) are cited **qualitatively** as corroboration of practice-based RWA variation; no numeric benchmark is extracted from them.

## 3. Results

**Capital dispersion (T8a).** Across 118 complete specification×seed draws of the $45B book:

| stat | required Pillar-1 capital |
|---|---|
| min | $2.02B |
| P25 | $2.91B |
| median | $3.17B |
| P75 | $3.66B |
| max | $4.22B |
| **range** | **$2.19B = 69% of median (4.87% of book notional)** |
| **primary (non-accumulating): E\|Δcapital\| per comparison** | **$0.65B = 20.5% of median** |

**Decomposition — design, not noise.** Portfolio-capital variance across draws: **design axes 71.0%**, **seed noise 0.03%**, residual 29.0%. The single largest axis is **A7 presentation (34.3%)**, then provider (12.5%) and few-shot (12.1%); temperature 0.5%. Reseeding an identical specification barely moves required capital; **re-specifying it moves capital by hundreds of millions.** This mirrors the T2 rating-unit finding (presentation the largest systematic lever) now expressed in dollars of regulatory capital.

**Not a saturation artefact.** 30 of 45 names have a verdict that reaches CCC-or-worse (hitting the 150% ceiling) in at least one specification. Removing them and recomputing on the 15 non-saturating names, the expected pairwise gap **rises** from 20.5% to **26.8%** — dispersion does not collapse; it is not merely the sub-BB− ceiling being toggled. Robustness holds under value-weighting (Zipf, identity-agnostic, no real-firm data: 22.3%) and under strict/tolerant parse rules (21.3% / 20.4%).

**Machine vs RCAP (T8b).** RCAP: outlier banks ~20% relative dispersion (2pp off a 10% benchmark) on the same portfolios via IRB models. Machine: expected pairwise gap 20.5%; outlier specifications deviate +33%/−36% from their median. The machine's **central-tendency** pairwise dispersion is of the same order as RCAP's **outlier** dispersion; on the like-for-like outlier metric the machine spread is somewhat wider. **Units differ — calibration, not identity** (IRB internal models vs standardized ECRA; real supervised banks vs LLM specifications; capital-ratio pp vs relative capital-$). We do not claim specifications are banks.

**Vendor error correlation (T8c).** Treating each specification as an institution holding the same book, the per-name capital error (deviation from the cross-spec mean) is correlated **within vendor (ρ_same = 0.068)** but not **across vendors (ρ_diff = −0.048)**; gap **+0.116** (xAI highest within-vendor, 0.137). Positive same-vendor correlation is modest in level but directionally clean: homogeneous vendor adoption converts idiosyncratic rating noise into a **common, non-diversifiable factor**.

## 4. Reviewer-attack items

**(xii) "Specifications aren't banks and standardized isn't IRB, so the RCAP comparison is invalid."** Conceded on units. The comparison is a calibration anchor — it places specification-induced capital dispersion on the same axis as the cross-bank dispersion regulators already judged large enough to warrant policy action. Same spirit as the T6 human-benchmark framing: same order of magnitude, measured honestly with different instruments.

**(xiii) "You never show market impact."** Conceded — T8 runs no market simulation. It establishes only the **precondition** for the transmission channel: same-vendor capital errors are positively correlated (ρ_same > ρ_diff). The step from correlated capital errors to procyclical deleveraging / fire-sale amplification is **cited, not simulated** (Llacay & Peffer, Finance Research Letters 2026; the RCAP policy concern with practice-based RWA variation). Market-impact modelling is explicitly scoped out as future work.

## 5. Reproduction

```
python3 03_analysis/capital_analysis.py     # -> results_capital.json
python3 04_exhibits/make_exhibits_t8.py      # -> T8a (csv+png), T8b (csv), T8c (csv)
```

Inputs: `02_panel/panel.parquet` (MANIFEST_PANEL 84ad8ebd) and `00_frozen_inputs/capital_map.json` (MANIFEST_CAPITAL, sha256 6a658726…). No network, no model calls at analysis time.
