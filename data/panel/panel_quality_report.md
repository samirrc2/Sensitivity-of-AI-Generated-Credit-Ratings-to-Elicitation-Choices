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

**Reading.** Low letter-count / low entropy = central-tendency compression; reported so that compression cannot be mistaken for stability in the granularity analysis (B3.7).