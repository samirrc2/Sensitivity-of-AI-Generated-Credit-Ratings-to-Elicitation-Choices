# Prompt Choice Alone Moves AI Credit Ratings Across the Investment-Grade Line

Reproducibility artifact for the *Scientific Reports* (Springer Nature) submission of the same title.

**Authors:** Samir Chincholikar (Independent researcher, New York, USA) · Robin Chawla (Independent researcher, New York, USA, corresponding author)
**ORCID:** [0009-0007-2779-3492](https://orcid.org/0009-0007-2779-3492) · [0009-0007-2807-3948](https://orcid.org/0009-0007-2807-3948)
**Contact:** robin.chawla.cse14@iitbhu.ac.in · samir.chincholikar@gmail.com
**Repository:** https://github.com/samirrc2/prompt-choice-credit-ratings
**Zenodo DOI:** *(minted at deposit — add `https://doi.org/10.5281/zenodo.…`)*

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
- The disposable SEC 10-K / company-facts cache used to *build* the real-firm battery is not shipped
  and is **not needed to reproduce any result**. It is re-fetchable for free from the public SEC
  EDGAR system (keyless; a descriptive `User-Agent` header is the only requirement,
  <https://www.sec.gov/os/webmaster-faq#developers>):
  - **10-K filings** — the permanent document URL for every issuer is in the `url` column of
    `data/frozen/realarm/ratings_provenance.csv` (e.g. `https://www.sec.gov/Archives/edgar/data/<CIK>/<ACCESSION>/<doc>.htm`); the `efts_verify` column gives the matching EDGAR full-text-search link.
  - **Company facts (XBRL)** — `https://data.sec.gov/api/xbrl/companyfacts/CIK<10-digit-CIK>.json`
  - **Filing index / submissions** — `https://data.sec.gov/submissions/CIK<10-digit-CIK>.json`
  The collector that rebuilds the cache from these endpoints is `capture/realarm_collect.py`.
- Manifest hashes in `manifest/` fix every frozen stage.
