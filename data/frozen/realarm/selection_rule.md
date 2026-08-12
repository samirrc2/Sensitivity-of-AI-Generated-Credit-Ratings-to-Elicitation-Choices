# Appendix D — Real-firm robustness arm: SELECTION RULE (frozen before pull)

*Mechanical, stated in advance. No hand-picking. The collector applies this rule in order and
freezes the result. This document is hashed into `MANIFEST_REALARM`.*

## Universe screen (FMP stock screener)
- Country = US; actively trading; common stock (exclude ETFs/funds).
- Market cap band **$2B–$15B** (mid-cap, to reduce memorization salience).
- **Exclude** GICS sector **Financials** and **Real Estate** (Altman Z″ inapplicable to
  banks/insurers/REITs). Implemented as FMP sector NOT IN {"Financial Services", "Real Estate"}.

## Ordering (deterministic, no discretion)
- Candidates sorted ascending by **ticker symbol** (stable, reproducible key). The pull walks this
  order; the first names passing QC fill the sets.

## Per-issuer requirements (all must hold to PASS)
1. **Fundamentals complete** — non-null: total assets, total liabilities, book equity, EBIT,
   working capital (current assets − current liabilities), retained earnings, revenue. (Altman Z″
   inputs + presentation-template fields.)
2. **Current agency rating** — a long-term issuer credit rating from S&P (primary), else Moody's,
   disclosed in the issuer's most recent 10-K, with the filing dated **≤ 12 months** before the
   pull date. Rating extracted with a verbatim quoted sentence + permanent SEC URL + document
   SHA-256 (provenance row).
3. **No restatement flag** in the pull window (FMP `financial-scores` / statements consistency;
   flagged issuers are skipped and logged).

## Sector cap
- **≤ 5 issuers per GICS sector** (across the 10 non-excluded sectors), to avoid sector
  concentration. Enforced greedily in ticker order.

## Target band mix (match the constructed battery's 15/15/15)
- Benchmark bands map from the agency rating: **SAFE = investment grade (BBB−/Baa3 and above)**,
  **WATCH = BB+/Ba1 … B−/B3**, **DISTRESS = CCC+/Caa1 and below**.
- Target ≈ **15 SAFE / 15 WATCH / 15 DISTRESS** in the PRIMARY set. Filled in ticker order until
  each stratum reaches 15; a stratum that cannot be filled from the screened universe is reported
  as a documented coverage limitation (real CCC mid-caps that file clean 10-Ks disclosing a letter
  rating are scarce — this is expected and stated, not worked around).

## Sets
- First **45** passing QC, respecting the sector cap and band targets, in ticker order = **PRIMARY**.
- Next **15** passing = **RESERVE**, used only to substitute a PRIMARY issuer that later fails QC.
  **Every substitution is logged** (issuer out, reason, issuer in).

## Split-rating rule (frozen)
- If S&P and Moody's disagree: use **S&P**. If S&P absent, use **Moody's** mapped to the S&P scale.
- If neither is disclosed with a current letter: **exclude** (reserve-substitute).

## Amendment (logged before Phase-2 pre-registration freeze; data-availability driven)
- **Discovery reversed:** candidates are sourced by SEC EDGAR full-text search for issuers whose
  most recent 10-K prints a Moody's rating token (`reverse_discover.py`), intersected with the
  mid-cap screen. This directly finds rating-*disclosing* issuers (most 10-Ks reference ratings
  without stating the letter; only a minority print it).
- **Band target relaxed to the natural distribution.** The constructed battery's 15/15/15 balance is
  infeasible for real issuers: CCC/Caa mid-caps that file a clean 10-K disclosing a letter number
  only ~5-8 market-wide. Forcing 15/15/15 would misrepresent an IG-heavy universe. PRIMARY is filled
  to 45 in ticker order among rated issuers; the resulting band mix is REPORTED, not imposed.
- **Sector cap 5 -> 7 -> 10** to accommodate the real sector concentration of rated issuers.
- **S&P/Fitch discovery tokens added** (`BBB+ BBB- BB+ BB- CCC+ CCC-`, signed notches only) alongside
  Moody's tokens, to surface issuers that disclose an S&P/Fitch letter but not a Moody's one.
- **Balance-sheet identity for total liabilities.** Many issuers file `LiabilitiesAndStockholdersEquity`
  but no standalone `us-gaap:Liabilities` tag; total liabilities is recovered by the accounting
  identity L = A − Equity (or LSE − Equity). Equity fallbacks include partnership/LLC forms
  (`PartnersCapital`, `MembersEquity`). A data-completeness parse rule using an identity that holds by
  construction — not a threshold or discretion. Working capital / retained earnings remain optional
  (unclassified balance sheets); Z″ is computed only when classified figures exist.
- Rationale is a real feature of the corporate-credit universe, documented; not result-driven tuning.

## Amendment v2 — decontamination redesign (logged after Phase-3 fingerprint gate fired NO-GO; before any outcome/rating data exists)
*The Phase-3 fingerprint gate is anonymization QC that exists precisely to iterate the anonymization
before H1 runs. It fired NO-GO (22.2% of firms named by Gemini from the exact figures; hits clustered
on household-name consumer brands). H1 is untouched; no rating task has run. Two vectors identified,
two fixes:*

### (a) Per-issuer figure perturbation (kills the exact-figure lookup vector)
- Every dollar figure fed into the ANONYMIZED prompt is multiplied by a single per-issuer scale factor
  `s_i ~ LogUniform(0.6, 1.7)`, one seeded draw per issuer (seed frozen in the build script).
- Because ALL of an issuer's figures share the same `s_i`, every **ratio** (margins, leverage TL/TA,
  current ratio, RE/TA, EBIT/TA, book leverage) is **exactly preserved** — the credit-rating task is
  unchanged — while the absolute magnitudes no longer match any real filing, defeating figure lookup.
- REAL (unscaled) figures + the rating are retained in `sealed_crosswalk.json` for provenance/audit.

### (b) Brand-salience screen (kills the structural-fingerprint vector perturbation cannot)
- Structural shapes (negative equity, loss-plus-leverage) are scale-invariant, so perturbation alone
  cannot hide a *recognizable* firm. Screen the universe to **low-salience B2B** issuers.
- **Mechanical GICS-sector rule (no hand-picking):** EXCLUDE consumer-facing sectors
  {Consumer Cyclical, Consumer Defensive, Communication Services}; KEEP low-salience B2B
  {Industrials, Basic Materials, Utilities, Technology, Energy, Healthcare}, AND additionally exclude
  consumer-facing SIC ranges that the FMP sector label misclassifies as B2B (toys 3940-3949; passenger
  transport/cruise/airline 4100-4199 & 4400-4599; consumer lawn/garden 2870-2879; toiletries 2840-2844;
  beverages/food 2080-2099; household appliances 3630-3639; apparel 2300-2399). Applied before ticker-order
  fill; the resulting band mix is REPORTED, not imposed.
- **Induced bias, stated honestly:** distinctive-structure firms are disproportionately recognizable,
  so this screen trades some profile diversity for *demonstrated* decontamination — and that trade is
  the arm's entire point. A B2B mid-cap universe is one where "a person on the street knows this firm"
  is structurally close to false.

### Consequences
- The screened pool yields <45 from the existing pull (34 B2B rated), so a **re-pull under this amended
  rule is required** — a documented redesign iteration, new manifest version + changelog entry.
- The **entire 45-name sample changes**, so the Phase-3 fingerprint gate is re-run from scratch on the
  new sample (not just the 10 replacements). Same thresholds: <5% GO / 5-15% one substitution round /
  >15% NO-GO. If a B2B + perturbed universe still fingerprints >15%, that is itself a publishable
  finding (anonymized-real-firm evaluation may be infeasible at this model generation), and the
  appendix pivots from "we ran it" to "we show why it cannot be run."

## Freeze
- Outputs: `raw_pull.json`, `primary_set.json`, `reserve_set.json`, `ratings_provenance.csv`,
  this `selection_rule.md` → SHA-256 each → `MANIFEST_REALARM.sha256`. Collect once; no re-pulls
  after freeze.
