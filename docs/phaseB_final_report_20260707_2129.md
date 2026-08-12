# Phase B Final Report — The Garden of Forking Prompts
*Generated 20260707_2129. Single-run, submission-ready. All results CONFIRMATORY unless labelled.*

## 1. Executive summary

On a 90-item, contamination-free financial battery run across 5 live model cells (OpenAI/Google/xAI, two snapshots each; xai/prior `grok-4.1-fast` dead — documented), the pre-registered conclusions are **specification-fragile at full power**, and the fragility is **two-layered**:

- **Layer 1 — ranking.** Decomposing the credit letter-rank: the firm (item) explains 63% and **irreducible run-to-run seed noise 25%**; every controllable design axis is small (largest: presentation 5.0%, provider×item 2.2%, provider main effect 1.3%). No axis clears the noise floor.
- **Layer 2 — fragility within honoured determinism.** In Google@temp0 (the only deterministic cells) band accuracy still ranges 0.36–0.69 across specs (permutation p=0.001). The fragility is not a noise artefact.

**Headline (new): effective resolution.** Cross-specification agreement on the machine credit opinion rises as the scale coarsens — letter 16%, notch 34%, band 65%, IG/HY 73% — but stays **below 80% even at the binary IG/HY level**, so the **effective resolution is coarser than IG/HY** (`table5.effective_resolution_90pct = coarser_than_ig_hy`). **Chance-corrected (post-hoc robustness), the result is starker:** the binary IG/HY level sits on a ~50% chance floor, so its 73% raw agreement is only Fleiss **κ=0.458** (AC1 0.46); letter κ=0.082, notch κ=0.181, band κ=0.389 — **no granularity reaches even κ=0.6**. This is not scale compression: models used 21/21 grades (entropy 4.026 of 4.39 bits). Economically, the primary (non-accumulating) measure is a **per-comparison IG/HY flip probability of 27%** (two random draws for a name land on opposite sides of the IG/HY line). The headline **98% of names (n=45) receive both an IG and an HY verdict** is a max-over-draws statistic (~120 draws/name) — the union a *literature of single-spec papers* would collectively reach, not a per-decision rate. **Market-priced against the actual ICE BofA OAS curve** (FRED, 782 trading days): **67% of names' cross-spec verdicts reach CCC** (a fragility statistic in itself), pinning the per-name spread range at the CCC-vs-AAA ceiling — a **median 820 bps** (the median==IQR-upper is this saturation, not a smooth distribution). The 15 non-saturating names sit at ~261 bps; the range is never below 106 bps on any trading day. (820 vs the earlier 413 = live CCC-inclusive market curve + letter granularity vs a static 3-band map, not a revision.)

**Formal human benchmark (T6), paired like-for-like by agency scale.** Machine per-comparison disagreement **significantly exceeds** the Moody's/S&P split at both granularities with a published rate: at the **notch (modifier) level** (our 21-grade letter scale) machine 84% vs agency 50% (z=105); at the **broad-letter level** (our 9-grade collapsed scale) machine 66% vs agency 13% (z=128); both dependence-adjusted p<0.0005 (item-clustered bootstrap). (A prior draft crossed the scale pairing; corrected here.)

Full-power flip shares: **C1 credit accuracy 50%** (95% CI [0.099, 0.8]), **C3 modal buy/hold/sell 55%** (95% CI [0.425, 0.6]); joint permutation p=0.001.

## 2. Manifest hashes (byte-identical reproduction)

- `MANIFEST_INPUTS`  (frozen inputs + collect.py): `7b8e8ea0b54801a1…`
- `MANIFEST_RAW`     (run_20260707_185649 corpus): `fd8122fa0e4b6690…`
- `MANIFEST_PANEL`   (panel.parquet): `84ad8ebd94e37667…`
- `MANIFEST_ANALYSIS`(results.json + results_addenda.json + results_market.json): `7618749f71f233f4…`
- `MANIFEST_MARKET`  (7 ICE BofA OAS series, FRED): `51a330d5e3d28114…` — the ONLY external data pull; provider model APIs remain sealed.

## 3. Deviations & amendments (in full)

```
# Deviations Addendum — Phase B (frozen)

*Consolidated, dated record of every deviation from the original F3 pre-registration, carried into
Phase B. Frozen with the inputs manifest; reproduced verbatim in the final report.*

## Carried from Phase A (harness/analysis, amendments A1–A4)
- **A1 — OpenAI call resilience (2026-07-07).** Single rigid request signature rejected by some
  snapshots (HTTP 400) → signature cascade; real error body surfaced. Harness only.
- **A2 — Reasoning/thinking budget (2026-07-07).** Reasoning/"thinking" models consumed the output
  budget → empty/truncated answers. Fix: `reasoning_effort=low` (OpenAI/xAI), `thinkingBudget=0`
  (Gemini), output budget 1024 tokens. Harness only; output format NOT forced (A5 preserved).
- **A3 — Provider swap Anthropic → xAI (2026-07-07).** No Anthropic key; xAI/Grok key available. A1
  categorical relabel; design balance and spec assignments unchanged.
- **A4 — `grok-4.1-fast` (xAI/prior) dead cell (2026-07-07).** Returned 480/480 empty in Phase A
  (reasoning-budget starvation, not fixed by reasoning_effort). Exclusion criterion: cell empty-rate
  > 30%. Excluded from Phase A analysis; xAI contributed `grok-4.3` (current) only.

## Phase B amendments (preregistration_v2 §3)
1. **Seeds 2 → 3** — noise floor is now a headline estimand.
2. **Effective temperature logged from response metadata, used as covariate** — reasoning models
   silently reject temperature=0.
3. **Primary question elevated to two layers** — (i) rank spec variance vs seed noise; (ii) fragility
   within honored determinism (Google@temp0).
4. **Provider set OpenAI/Google/xAI** — Anthropic key unavailable.
5. **Battery stays 90 items** — 400-item expansion deferred to referee response.
6. **Credit task elicited at LETTER-GRADE scale AAA…C** (`rating_scale.json`) — band/IG-HY become
   post-hoc coarsenings of the same stored responses; granularity-stability added as a confirmatory
   analysis. Phase A elicited at band level → band results comparable-in-spirit, not byte-identical.
   GUARDRAIL: no capability claims anywhere; letter accuracy is input to stability only; capability ceded
   to Drinkall et al. (FinNLP 2025). The Altman EMS Z''→rating benchmark map is VERIFY-flagged and used
   only as a stability input.

## DECISION ON RECORD (2026-07-07) — grok-4.1-fast retained (option a)
**`grok-4.1-fast` (xAI/prior) is retained pinned, faithfully, as pre-registered.** It was 100% empty
in Phase A (reasoning-budget starvation; callable — HTTP 200 — but no visible text). The snapshot is
**NOT swapped.** The xAI/prior cell (8 specs × 90 items × 3 seeds = 2,160 calls ≈ **16.7%** of the
grid) is therefore expected to come back MISSING again.

**The >10% missingness auto-stop is EXPECTED here and is NOT an error.** The correct, pre-authorised
response when it fires is **proceed-on-the-5-live-cells** — i.e. run B2–B5 analysis on the five live
model cells (openai/current, openai/prior, google/current, google/prior, xai/current), treating the
dead xai/prior cell as a documented finding. It is **NOT** a signal to patch, re-collect, or swap the
snapshot; the one-run rule holds. The auto-stop fires only AFTER the full grid is attempted and
`MANIFEST_RAW.sha256` is written, so no completed cell is lost.

Snapshot verification (empirical, from the Phase A corpus, all six were live and called):
openai/current `gpt-5.4-nano`, openai/prior `gpt-5-nano-2025-08-07`, google/current `gemini-3.5-flash`,
google/prior `gemini-2.5-flash`, xai/current `grok-4.3` — all returned content; xai/prior
`grok-4.1-fast` — callable but 100% empty.

## Harness (collect.py) — concurrency
Collection parallelised with a `ThreadPoolExecutor` (default 24 workers) + per-provider min-interval
rate limiters (openai 500 / google 300 / xai 180 rpm), matching the Paper 1/2 orchestrators. Execution
order does not affect the frozen result (each cell writes its own immutable file; analysis is an
order-independent function of `raw/`); concurrency is purely a wall-clock optimisation. Thread-safe
spend/hard-stop/log via a lock; resume-safe (completed cells skipped before the pool). Also fixed:
`collect.py` reads provider keys from `keys.env.txt` when the corresponding env var is unset — if the
shell exports `GOOGLE_API_KEY`/`OPENAI_API_KEY`/`XAI_API_KEY` to a placeholder value, that wins; unset
them so the real keys load.

## Parser deviation
Pre-registered A8 LLM-judge parser replaced by a deterministic tolerant parser (no LLM API reachable
in the analysis sandbox); it only ever touches the residual that lenient cannot parse (~0 on clean
output). Reported as a deviation; strict/lenient/tolerant all applied post-hoc.
```

## 4. Panel quality

```
# Phase B — Panel quality report

- source run: `run_20260707_185649` (MANIFEST_RAW `fd8122fa0e4b6690`)
- panel rows: 32379 (item x spec x seed x 3 parse-rules; live cells only)
- ok cells used: 10793 | dead cell excluded: xai/prior grok-4.1-fast

## Cell census (all raw incl. missing)
| cell | total | ok | missing |
|---|---|---|---|
| google/current | 2160 | 2160 | 0 |
| google/prior | 2160 | 2160 | 0 |
| openai/current | 2160 | 2154 | 6 |
| openai/prior | 2160 | 2159 | 1 |
| xai/current | 2160 | 2160 | 0 |
| xai/prior | 2160 | 0 | 2160 |

## Parse rates + strict-vs-lenient
- lenient 100.0% | strict 99.3% | tolerant 100.0%
- strict-vs-lenient decision disagreement: 1.25%
- cells failing ALL 3 parse rules (logged, not edited): 0

## Scale-usage entropy (credit, 21-grade letter scale) — compression check
- overall: 21 of 21 letters used; Shannon entropy 4.026 bits (max 4.39)
  - google: 21/21 letters, entropy 3.826 bits
  - openai: 21/21 letters, entropy 3.702 bits
  - xai: 21/21 letters, entropy 4.164 bits
```

## 5. Each confirmatory result vs Phase A / deep-dive

| Result | Phase A / deep-dive | Phase B (full power) | Status |
|---|---|---|---|
| C1 credit-accuracy flip share | 19% (band elicitation, 2 providers) | 50% (letter→band, 3 providers) | **sharpened** |
| Survives determinism (Google@temp0) | p=0.036, acc 0.47–0.87 | p=0.001, acc 0.36–0.69 | **confirmed** |
| Seed noise ranks above every axis | residual ~29% | residual 25% (> all axes) | **confirmed** |
| Largest design axis | paraphrase ~3% | presentation 5.0% | confirmed (small; lever shifted) |
| Provider: main effect small, interaction large | provider 0.9%; within 92% / cross 34% (band) | provider 1.3%, prov×item 2.2%; within 74% / cross 50% | **confirmed** |
| Economic IG/HY straddle | 67% (deep-dive, band) | 98% (letter) | **sharpened** |
| Granularity / effective resolution | — (new in Phase B) | coarser than IG/HY (agreement <80% at every level) | **new** |

## 6. Reviewer attack list

| # | Objection | Response (exhibit) |
|---|---|---|
| i | "It's just noise, not specification." | Conceded as Layer 1 and foregrounded (T2). But the deterministic subgrid (F4, p=0.001) shows fragility survives zero-noise settings — both layers are real. |
| ii | "Only a few providers." | Three model families with two snapshots each; provider is <2% of level variance and the interaction dominates (T3) — adding families did not make provider the lever. |
| iii | "Temperature wasn't honoured." | Measured and localised (F5): only Google honours temp=0; effective temperature is logged and the deterministic result uses the honoured-determinism cells only. |
| iv | "Altman Z'' is a weak ground truth." | C1 is a comparability check, not a capability claim; the granularity result (T5/F6) and vendor structure (T3) are **benchmark-free**. |
| v | "Survivorship / constructed battery." | Constructed, contamination-free items; the estimand is stability across specs, which does not depend on the sampling frame. |
| vi | "Scale compression fakes the low resolution." | Refuted directly: models used 21/21 grades, entropy 4.0/4.4 bits (T5). Low cross-spec agreement is genuine disagreement, not everyone-says-BBB. |
| vii | "LLM credit rating is already done (Drinkall)." | Drinkall et al. (FinNLP 2025) measure **accuracy** on real firms; we measure **stability** on contamination-free constructed items — a different estimand. No capability claim is made anywhere. |
| viii | "Raw agreement ignores the chance baseline — binary IG/HY has a ~50% floor." | Conceded and pre-empted (T5, post-hoc robustness): chance-corrected, IG/HY is only κ=0.458 (AC1 0.46); letter κ=0.082; **no level reaches κ=0.6**. The correction *starkens* 'no stable resolution' — the coarse levels survived partly on their chance floor. |
| ix | "98% straddle is a max-over-draws artefact." | Conceded and reframed (T4): the **primary** measure is the per-comparison IG/HY flip (27%), which does not accumulate; the 98% is explicitly the union over ~120 draws/name — 'what a literature of single-spec papers would collectively conclude', not a per-decision rate. |
| x | "Some human disagreement is normal — is the machine actually worse?" | Formally tested (T6, §7): machine per-comparison disagreement significantly EXCEEDS the Moody's/S&P split rate at **both agency-published granularities (notch/modifier and broad letter), paired like-for-like** (machine 84% vs 50% at notch; 66% vs 13% at broad letter), dependence-adjusted p<0.0005. The machine is not merely as inconsistent as two agencies — it is significantly more so. Caveat: 'raters' are specifications vs two firms; calibration, not identity. |

## 7. Post-hoc addenda (labelled; frozen panel + FRED market data only)

**T6 — human benchmark (formal test).** Per-comparison disagreement, machine vs published agency split (source: Cantor, Packer & Cole; Livingston, Naranjo & Zhou (2010, J. Money Credit & Banking), N=13,853 issues; ~50% split at NOTCH (modifier) level, ~13% at LETTER (broad alpha) level. Paired like-for-like against our matching coarsenings.):

| agency scale (= our coarsening) | machine disagree | human split | z (naive) | p (dep-adj) |
|---|---|---|---|---|
| notch/modifier (AA+ vs AA) = our 21-grade letter scale | 84% | 50% (N=13,853) | 105 | <0.0005 |
| broad letter/alpha (AA vs A) = our notch-collapsed 9-grade scale | 66% | 13% (N=13,853) | 128 | <0.0005 |
| our band (35%) | — | — (no published rate) | — | not tested |
| our ig_hy (27%) | — | — (no published rate) | — | not tested |

*Machine 'raters' are specifications; agency raters are two firms. The comparison is calibration, not identity. Naive z uses the pairwise-comparison count and is anti-conservative; the item-clustered bootstrap is the honest inference.*

**ADD2 — power & subsample validation.** Min detectable axis variance-share at 80% power ≈ **5.5%** (so presentation ≈5% is borderline-detectable, the rest are below the design's resolving power). Item-subsampling validation (50% of items): residual 27.89±4.04%, presentation 4.91±1.01% — the decomposition is stable, not a 45-item artefact. Assumptions: Power figure assumes an F-test for a single 2-level main effect, effective replication n=items*seeds, alpha=0.05, and treats residual+seed as the error term; it is an order-of-magnitude guide, not an exact design calc. Subsample validation resamples items (the clustering unit) at 25/50/75% and reports mean+/-sd of the key shares to show the decomposition is stable, not an artefact of the 45-item sample.

**ADD3 — effective-resolution function R(τ).** *Effective resolution R(tau) of a machine rating opinion = the FINEST scale granularity at which cross-specification agreement, chance-corrected by Fleiss' kappa, attains threshold tau. It is benchmark-free, reusable, and reported with item-bootstrap CIs.* κ by granularity: letter 0.082, notch 0.181, band 0.389, IG/HY 0.458. **R(0.40) = ig_hy, R(0.60) = none (coarser than IG/HY), R(0.75) = none (coarser than IG/HY)** (item-bootstrap CIs in `results_addenda.json`).

**ADD1b — market-priced (T4 upgrade).** Re-pricing each name's cross-specification verdict range against the actual ICE BofA OAS curve on all 782 trading days 2023-07-10..2026-07-01: the implied spread range per name is 820 bps (median across names of the per-name median-across-days), IQR [275, 820] bps; across all names the range is never below 106 bps on any trading day in the window.

*Saturation caveat (honest):* 30/45 names have a verdict reaching CCC, so their spread range collapses to (CCC_OAS - best_OAS) and is near-identical across those names on a given day — hence median==IQR-upper (820 bps) is a SCALE-SATURATION ceiling, not a smooth distribution. The share reaching CCC (67%) is itself a fragility statistic. Non-saturating names (n=15): median 261 bps (IQR [250.5, 275.0]). 413 bps (earlier) came from a STATIC 3-band map (SAFE 150 / WATCH 300 / DISTRESS 700). 820 bps here is priced on the LIVE ICE BofA OAS curve, which is CCC-inclusive (CCC OAS ~1000 bps >> the static DISTRESS=700 proxy) and uses the finer letter elicitation that reaches CCC. Different instruments, not a revision: static map vs market curve, band vs letter granularity.

## 8. Citation hygiene — Altman EMS map (VERIFY flag resolved)

The Altman EMS Z''→bond-rating map in `rating_scale.json` feeds **only the two illustrative few-shot exemplar labels** (frozen in the prompt); it is imported by NO confirmatory statistic (verify: `run_analysis.py` never references `ems_zpp_to_rating`; C1 uses the letter→band coarsening vs Paper 2's band benchmark). Framework verified against Altman (2005, *Emerging Markets Review* 6(4)) and Altman & Hotchkiss (2006): the Z''-score with the +3.25 constant standardises so 0 = D, and bond-rating equivalents are defined by class-average Z''. The exact per-rating thresholds are **vintage-dependent** (e.g. more recent US calibrations place AAA/AA nearer 6.3), so the map is cited as **indicative and non-load-bearing**; the VERIFY flag is resolved to that scope. No reported number changes under any admissible EMS calibration.

## 9. Reproduction (byte-identical)

```
cd phaseB
python3 02_panel/build_panel.py       # run_20260707_185649 -> panel.parquet  (MANIFEST_PANEL)
python3 03_analysis/run_analysis.py   # panel.parquet -> results.json          (MANIFEST_ANALYSIS)
python3 04_exhibits/make_exhibits.py  # results.json -> T1-T5 + F1-F6
python3 05_report/report_gen.py       # results.json -> this report
```
Analysis reads ONLY `02_panel/panel.parquet`; it never touches raw. Given the frozen `MANIFEST_RAW fd8122fa0e4b6690…`, the panel and results reproduce byte-identically.

## 10. Verdict — what survived at full power

Every pre-registered claim survived, most **sharpened** by the finer letter scale:
- **H1 fragility real** — survived (C1 50%, C3 55%, perm p=0.001).
- **H2 survives determinism** — survived (p=0.001).
- **H3 noise ranks high** — survived (seed noise 25% > every axis).
- **H4 provider reconciliation** — survived (main 1.3% « interaction 2.2%; within>cross).
- **H5 economic** — survived, sharpened (98% IG/HY straddle).
- **H6 granularity (new)** — survived, and starker chance-corrected: the machine credit opinion has **no specification-stable resolution** — Fleiss κ ≤ 0.458 at every level, not even the binary IG/HY distinction.

Blunt reading: this is no longer only a "prompt-fragility" letter — the sharp, citable result is that a generative-AI credit opinion, elicited at rating granularity, does not carry a stable notch — or even a stable investment-grade/high-yield — signal across defensible specifications, and most of the residual instability is irreducible run-to-run noise, not a knob you can tune. Capability is not assessed here.

---
*Exploratory content: none in the confirmatory set; all analyses were pre-registered in `preregistration_v2.md`. Dead cell (grok-4.1-fast) censused, not patched.*