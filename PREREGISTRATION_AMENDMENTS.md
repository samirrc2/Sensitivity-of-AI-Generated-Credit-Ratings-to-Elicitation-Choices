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
