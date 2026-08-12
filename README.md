# Prompt Choice Alone Moves AI Credit Ratings Across the Investment-Grade Line

Reproducibility artifact for the manuscript of the same title (targeting *Scientific Reports*;
originally drafted for *Finance Research Letters*).

**Authors:** Samir Chincholikar (Independent researcher) · Robin Chawla (corresponding author,
affiliation pending)

Every number, table, and figure regenerates from a **frozen response corpus** (90-item battery ×
48 specifications × 3 seeds ≈ 12,960 elicitations across three model families) plus a
**decontaminated real-firm robustness arm** (31 anonymized, perturbed issuers benchmarked to
disclosed agency ratings) — **offline, with no API calls and at zero cost.**

## Repository layout
```
config/            # grid, paraphrase templates, rating scale, run config
capture/           # collection code (agent/orchestrator, real-firm collector) — NOT needed to reproduce
analysis/          # confirmatory analysis: run_analysis, capital, market, addenda,
                   #   benchmark_validation, analyze_realarm  (all offline)
data/
  frozen/main/     # battery_90, grid, capital_map, rating_scale, manifests (pre-registered inputs)
  frozen/realarm/  # real-firm arm frozen artifacts (battery, sealed crosswalk, provenance, spec grid)
  frozen/market_data/  # FRED spread series (cached)
  raw/main/        # frozen response corpus (per-call JSON)
  raw/realarm/     # real-firm arm model-output run panels (arm/comparator/fingerprint)
  panel/           # panel.parquet (built once from raw; the analysis input)
results/           # regenerated results_*.json, H1_results.json, exhibits/ (figures + tables)
paper/
  scientific_reports/  # Scientific Reports manuscript (sn-jnl template) + figures + cover letter
docs/              # reports, appendix D, changelog
manifest/          # SHA-256 manifests for every frozen stage
PREREGISTRATION.md, PREREGISTRATION_AMENDMENTS.md
README.md, LICENSE, CITATION.cff, DATA_AVAILABILITY.md, reproduce.sh
```

## Reproduce (offline, no keys)
```bash
pip install numpy pandas pyarrow matplotlib pyyaml
bash reproduce.sh
```
All `results/results_*.json`, `results/H1_results.json`, and `results/exhibits/*` regenerate
byte-for-byte from the frozen data (verified). Confirmatory headline:
`primary Δκ(HOM−HET) = 0.336`; real-arm WATCH-stratum flip-share difference `−0.09 (inside ±0.15)`.

## Notes
- `capture/` is provided for transparency only; reproduction never calls a model API.
- The disposable SEC 10-K / company-facts cache used to *build* the real-firm battery is not shipped;
  it is re-fetchable at no cost from the accession IDs in `data/frozen/realarm/ratings_provenance.csv`
  and is not needed to reproduce any result.
- Manifest hashes in `manifest/` fix every frozen stage.
