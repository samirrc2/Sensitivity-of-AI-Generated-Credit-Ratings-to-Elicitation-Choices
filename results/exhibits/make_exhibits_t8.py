"""T8 (POST-HOC ADDITION, labelled) — capital-recast exhibits.
Deterministic from 03_analysis/results_capital.json.
  T8a_capital_dispersion (.csv + .png)   machine RWA/capital dispersion on the frozen book
  T8b_regulatory_benchmark (.csv)        machine vs BCBS 256 RCAP cross-bank dispersion
  T8c_vendor_correlation (.csv)          within- vs cross-vendor capital-error correlation
"""
from __future__ import annotations
import json, csv
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PB = Path(__file__).resolve().parents[1]
C = json.load(open(PB / "03_analysis" / "results_capital.json"))
E = PB / "04_exhibits"; E.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 150, "font.size": 11, "font.family": "DejaVu Sans",
                     "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 12, "axes.labelsize": 11,
                     "savefig.bbox": "tight"})

def wcsv(name, header, rows):
    with open(E / name, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)

b = C["capital.base"]; dist = b["capital_distribution_usd"]; dec = C["capital.decomposition"]
prim = C["capital.primary_number_for_main_text"]; coll = C["capital.saturation_collapse_check"]
rob_ex = C["capital.robustness_exclude_saturating"]; rob_vw = C["capital.robustness_value_weight"]
M = 1e6

# ---------- T8a CSV: distribution + primary + decomposition + robustness ----------
rows = [
 ["scope", f"Pillar 1 min @ 8%, ECRA base RW (CRE20.42), equal-weight $1B/name, 45 names, {b['n_draws']} draws"],
 ["book_total_notional_usd", "%.0f" % b["total_notional_usd"]],
 ["capital_min_usd", "%.0f" % dist["min"]], ["capital_p25_usd", "%.0f" % dist["p25"]],
 ["capital_median_usd", "%.0f" % dist["median"]], ["capital_p75_usd", "%.0f" % dist["p75"]],
 ["capital_max_usd", "%.0f" % dist["max"]],
 ["capital_range_usd", "%.0f" % b["capital_range_usd"]],
 ["capital_range_pct_of_median", "%.2f" % b["capital_range_pct_of_median"]],
 ["capital_range_pct_of_notional", "%.3f" % b["capital_range_pct_of_notional"]],
 ["PRIMARY_expected_abs_capital_diff_per_comparison_usd", "%.0f" % prim["value_usd"]],
 ["PRIMARY_expected_abs_capital_diff_pct_of_median", "%.2f" % prim["value_pct_of_median_capital"]],
 ["decomp_design_axes_pct", "%.2f" % dec["design_axes_total_pct"]],
 ["decomp_seed_noise_pct", "%.2f" % dec["seed_noise_pct"]],
 ["decomp_residual_pct", "%.2f" % dec["residual_pct"]],
 ["robust_valueweight_range_pct_of_median", "%.2f" % rob_vw["capital_range_pct_of_median"]],
 ["robust_valueweight_expected_abs_diff_pct", "%.2f" % rob_vw["expected_abs_capital_diff_pct_of_median"]],
 ["robust_exclude_saturating_n_names", "%d" % rob_ex["n_names"]],
 ["robust_exclude_saturating_expected_abs_diff_pct", "%.2f" % rob_ex["expected_abs_capital_diff_pct_of_median"]],
 ["n_saturating_names_reach_CCC", "%d" % coll["n_saturating_names_reach_CCC"]],
 ["collapses_without_saturating_names", str(coll["collapses_without_saturating_names"])],
]
wcsv("T8a_capital_dispersion.csv", ["metric", "value"], rows)

# ---------- T8a PNG: histogram of portfolio required capital across draws ----------
cap = np.array(C["_cap_vector_base"]) / 1e9   # $B
fig, ax = plt.subplots(figsize=(8.5, 4.6))
ax.hist(cap, bins=18, color="#3b6ea5", edgecolor="white", alpha=0.9)
med = dist["median"] / 1e9
ax.axvline(med, color="#b3202c", ls="--", lw=1.8, label=f"median ${med:.2f}B")
ax.axvline(dist["min"]/1e9, color="#555", ls=":", lw=1.4, label=f"min ${dist['min']/1e9:.2f}B")
ax.axvline(dist["max"]/1e9, color="#555", ls=":", lw=1.4, label=f"max ${dist['max']/1e9:.2f}B")
ax.set_xlabel(r"required Pillar-1 minimum capital for the SAME \$45B book (\$B)")
ax.set_ylabel("number of specifications (draws)")
ax.set_title("T8a · Same book, %d specifications: capital swings %.0f%% (E|Δ|=%.0f%%, seed noise≈%.0f%%)"
             % (b["n_draws"], b["capital_range_pct_of_median"], prim["value_pct_of_median_capital"],
                dec["seed_noise_pct"]))
ax.annotate(f"expected pairwise gap\n${prim['value_usd']/1e9:.2f}B = {prim['value_pct_of_median_capital']:.0f}% of median",
            xy=(0.98, 0.72), xycoords="axes fraction", ha="right", fontsize=9.5,
            bbox=dict(boxstyle="round", fc="#fff3d6", ec="#c9a227"))
ax.legend(loc="upper left", fontsize=9)
fig.savefig(E / "T8a_capital_dispersion.png"); plt.close(fig)

# ---------- T8b CSV: machine vs RCAP benchmark ----------
bm = C["capital.regulatory_benchmark_RCAP"]
wcsv("T8b_regulatory_benchmark.csv", ["source", "metric", "relative_dispersion_pct", "note"], [
 ["BCBS 256 RCAP (2013)", "outlier bank vs 10% capital-ratio benchmark", "%.1f" % bm["rcap_headline_relative_dispersion_pct"],
  "= 2.0 pp either direction; IRB internal models; >100 banks; OUTLIER figure, most banks narrower"],
 ["Machine (this study)", "expected pairwise gap (central tendency)", "%.2f" % bm["machine_expected_pairwise_relative_pct"],
  "standardised ECRA; 45-name synthetic book; MEAN over spec pairs, not an outlier"],
 ["Machine (this study)", "outlier spec above median", "%.1f" % bm["machine_outlier_deviation_from_median_pct"]["above_median"],
  "like-for-like with RCAP outlier metric"],
 ["Machine (this study)", "outlier spec below median", "%.1f" % bm["machine_outlier_deviation_from_median_pct"]["below_median"],
  "like-for-like with RCAP outlier metric"],
 ["Machine (this study)", "full range", "%.1f" % bm["machine_full_range_relative_pct"], "max-min as % of median"],
])

# ---------- T8c CSV: vendor error correlation ----------
vc = C["capital.vendor_error_correlation"]
rows = [["same_vendor_mean", "%.3f" % vc["rho_same_vendor"], "%d" % vc["n_same_pairs"], "within-vendor spec pairs"],
        ["diff_vendor_mean", "%.3f" % vc["rho_diff_vendor"], "%d" % vc["n_diff_pairs"], "cross-vendor spec pairs"],
        ["gap_same_minus_diff", "%.3f" % vc["gap_same_minus_diff"], "", "systemic (non-diversifiable) component"]]
for k, v in vc["rho_same_by_vendor"].items():
    rows.append(["same_vendor_%s" % k, "%.3f" % v, "", "within-%s correlation" % k])
wcsv("T8c_vendor_correlation.csv", ["pair_type", "mean_capital_error_correlation", "n_pairs", "note"], rows)

print("wrote T8a (csv+png), T8b (csv), T8c (csv) to 04_exhibits/")
print("  T8a capital range %.0f%% of median | E|Δ| %.0f%% | design %.0f%% seed %.0f%%"
      % (b["capital_range_pct_of_median"], prim["value_pct_of_median_capital"],
         dec["design_axes_total_pct"], dec["seed_noise_pct"]))
print("  T8b machine outlier +%.0f/-%.0f%% vs RCAP ~20%%" % (
    bm["machine_outlier_deviation_from_median_pct"]["above_median"],
    bm["machine_outlier_deviation_from_median_pct"]["below_median"]))
print("  T8c rho_same %.3f  rho_diff %.3f  gap %.3f" % (vc["rho_same_vendor"], vc["rho_diff_vendor"], vc["gap_same_minus_diff"]))
