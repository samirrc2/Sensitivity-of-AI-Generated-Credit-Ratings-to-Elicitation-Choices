# Pre-registration v2 — Phase B (single, submission-ready run)
## "The Garden of Forking Prompts: A Specification-Curve Analysis of Generative AI in Finance"

*Frozen before Phase B collection. Phase A + deep-dive are complete and frozen; this document
carries them forward and states, dated and reasoned, every Phase B amendment. Collection happens
EXACTLY ONCE. Failures are data. No new axes, hypotheses, or post-hoc factors are introduced.*

---

## 1. Instrument (carried forward, verbatim)
90-item battery from Paper 2 (`battery_90.json`): 45 credit_health items (Altman Z″ band:
SAFE/WATCH/DISTRESS) + 45 directional items (BUY/HOLD/SELL vs 20-td forward-return sign; HOLD =
abstention). Loaded as-is; labels unmodified. Full 90 items (Phase A used a 30-item subset).

## 2. Design (carried forward)
48-specification balance-constrained D-optimal fraction of the 288-cell A1–A7 factorial
(`grid_definition.json`): A1 provider {OpenAI, Google, xAI} × A2 version {current, prior} × A3
temperature {0.0, 1.0} × A4 paraphrase {P1,P2,P3} × A5 format {json, freetext} × A6 few-shot {0,2}
× A7 presentation {L0 prose/original, L1 table/reversed}. A8 parsing {strict, lenient, tolerant}
applied POST-HOC to stored text. Resolution reported, not assumed: main effects mutually orthogonal
(max |r| = 0.054); main × two-factor-interaction aliasing up to 0.354 (only low-alias 2FIs
estimable). Generator + proof in `grid_definition.json`.

## 3. Amendments (Phase A → Phase B), each dated and reasoned
1. **Seeds 2 → 3 (2026-07-07).** The noise floor is now a headline estimand (deep-dive established
   run-to-run noise ≈ 30% of variance and that fragility survives determinism). Three seeds give a
   more stable within-cell noise estimate. Seeds = [11, 22, 33].
2. **Effective temperature logged and used as a covariate (2026-07-07).** Phase A discovered that
   OpenAI and xAI reasoning models silently reject `temperature=0`. Phase B logs the applied/effective
   temperature from each response's request echo/metadata and treats it as a covariate, not an
   assumed factor level.
3. **Primary question elevated to two explicit layers (2026-07-07):** (i) *ranking* researcher-choice
   (specification) variance against run-to-run (seed) noise; (ii) *fragility within honored
   determinism* — the Google@temp0 subgrid. Both are confirmatory in Phase B.
4. **Provider set = OpenAI / Google / xAI (2026-07-07).** Pre-registered Anthropic dropped (no API
   key available); xAI/Grok substituted. A1 categorical relabel only; design balance preserved.
5. **Battery stays 90 items (2026-07-07).** A ~400-item expansion (deep-dive power calc: ~414 credit
   items for a ±5pp flip-share CI) is deferred to referee response, not run now.
6. **Credit task elicited at LETTER-GRADE scale AAA…C (2026-07-07).** The credit family now asks for a
   21-grade issuer letter rating (`rating_scale.json`); notch-collapsed, band (SAFE/WATCH/DISTRESS), and
   IG/HY are **deterministic post-hoc coarsenings of the SAME stored responses** → granularity is a
   zero-cost analysis dimension, not a new collection axis. The directional family is unchanged.

**NEW CONFIRMATORY ANALYSIS — granularity-dependence of specification stability.** Flip probability as a
function of scale coarseness (letter → notch-collapsed → band → IG/HY), on identical stored responses;
plus an **effective-resolution** statistic (the finest granularity at which the machine credit opinion is
stable in ≥X% of spec/seed comparisons, X = 80/90/95), reported alongside **scale-usage entropy** (how many
of the 21 letters models actually use) so that central-tendency compression cannot masquerade as stability.

**Phase A comparability note.** The Phase A pilot elicited the credit task at BAND level; Phase B elicits at
letter level and coarsens back to band for the C1 comparison. Band-level results are therefore
comparable-in-spirit, not byte-identical (the letter→band map is defined in `rating_scale.json`).

**GUARDRAIL — no capability claims (2026-07-07).** Letter-scale accuracy statistics are inputs to the
STABILITY analysis ONLY. The capability question — *can LLMs rate credit accurately* — is ceded to Drinkall
et al. (FinNLP 2025) in one sentence; **no capability claim appears anywhere** in Phase B. Our estimand is
stability/granularity of the opinion on a contamination-free constructed battery, a different question.

*No other change. No new axis, hypothesis, or post-hoc factor hunting.*

## 4. Confirmatory analysis plan (Phase B B3; reads the frozen panel only)
- **3.1 Noise floor:** seed disagreement by provider × requested-temp × effective-temp; Google@temp0
  as the honored-determinism reference.
- **3.2 Deterministic subgrid:** flip shares, accuracy range, permutation test within Google@temp0.
- **3.3 Variance decomposition:** mixed-effects on notch deviation + ordinal decision; variance
  shares for A1–A8, item, provider×item, residual (seed); bootstrap CIs on every share.
- **3.4 Spec curves:** C1 (majority-correct credit accuracy), C2 (directional bias sign), C3 (modal
  decision) at 90 items; flip shares with bootstrap CIs over items; permutation joint inference
  (1,000 seeded draws).
- **3.5 Vendor structure:** within- vs cross-family κ on identical items; <1% provider main effect vs
  large provider×item interaction (Paper 1 reconciliation).
- **3.6 Economic translation:** % names receiving both IG and HY verdicts (denominator stated);
  implied spread anchored to Cornaggia et al. (80–140 bps per 2–3 notches) + a cited rating-spread table;
  implied portfolio turnover.
- **3.7 Granularity-stability (NEW, confirmatory):** flip probability per spec-pair and seed-pair at each
  coarsening (letter → notch-collapsed → band → IG/HY) on the SAME stored responses; the granularity curve;
  the effective-resolution statistic (finest stable scale at ≥80/90/95% of comparisons); reported with
  scale-usage entropy. Benchmark-free.
- **3.8 Robustness:** drop-one-provider, drop-one-axis, parse-rule sensitivity, dead-cell treatment
  (exclusion vs conservative imputation) for every headline number.

## 5. Pre-registered claims to be tested at full power (from Phase A / deep-dive)
- **H1 (fragility real):** conclusion-flip share > 10% for ≥1 of C1/C3, permutation p < 0.05.
- **H2 (survives determinism):** within Google@temp0, accuracy range materially > 0 and permutation
  p < 0.05.
- **H3 (noise ranks high):** residual/seed variance share exceeds every design-axis main-effect share.
- **H4 (provider reconciliation):** provider main effect < ~2% of level variance AND within-family κ
  materially exceeds cross-family κ.
- **H5 (economic):** a material share of names cross the IG/HY line across specifications.
- **H6 (granularity, NEW):** flip probability rises monotonically with scale fineness; the effective
  resolution of the machine credit opinion is coarser than the notch level (i.e. letter-notch distinctions
  are not stable across specifications) — reported jointly with scale-usage entropy so compression is
  distinguished from stability.

## 6. One-run rule (governs collection)
Collection runs exactly once. After the run terminates and `MANIFEST_RAW.sha256` is written, **no cell
is ever re-collected for any reason.** Dead cells, refusals, and gaps are findings, reported not
patched. If total missingness > 10% of cells, collection STOPS after hashing and awaits instruction
(no silent patching). Empty completions after retries are recorded MISSING.

## 7. Hard constraints
Analysis (03) reads only the frozen panel (02), never raw (01). Exploratory results are labelled and
quarantined to an appendix. No fabrication/imputation of inconvenient cells; missing is missing. No
manuscript prose in any deliverable.
