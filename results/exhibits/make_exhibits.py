"""B4 — camera-ready exhibits. Deterministic from 03_analysis/results.json (+ spec_curves.json).
T1-T5 (.csv + .png) and F1-F6 (.png). exhibit_notes.md maps each to its claim + citation."""
from __future__ import annotations
import json, csv
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PB = Path(__file__).resolve().parents[1]
R = json.load(open(PB / "03_analysis" / "results.json"))
SC = json.load(open(PB / "03_analysis" / "spec_curves.json"))
ADD = json.load(open(PB / "03_analysis" / "results_addenda.json"))
MKT = json.load(open(PB / "03_analysis" / "results_market.json"))
E = PB / "04_exhibits"; E.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 150, "font.size": 11, "font.family": "DejaVu Sans",
                     "axes.grid": True, "grid.alpha": 0.25, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titlesize": 12, "axes.labelsize": 11,
                     "savefig.bbox": "tight"})
sp = R["block_spec"]; var = R["block_var"]["table2.variance_shares_pct_letterrank"]
ven = R["block_vendor"]; eco = R["block_econ"]; gr = R["block_gran"]; det = R["block_det"]; nz = R["block_noise"]


def wcsv(name, header, rows):
    with open(E / name, "w", newline="") as f:
        w = csv.writer(f); w.writerow(header); w.writerows(rows)


# ---------- T1 flip shares ----------
wcsv("T1_flip_shares.csv", ["conclusion", "flip_share", "ci_low", "ci_high", "note"], [
    ["C1_credit_accuracy_band", sp["abstract.flip_share_C1"], *sp["table1.C1_95CI_flip"], f"acc range {sp['table1.C1_accuracy_range']}"],
    ["C2_bias_sign", sp["table1.C2_flip_share"], "", "", f"modal median-notch sign {sp['table1.C2_median_notch_modal_sign']}"],
    ["C3_directional_modal", sp["abstract.flip_share_C3"], *sp["table1.C3_95CI_flip"], f"modal {sp['table1.C3_modal']}"]])
fig, ax = plt.subplots(figsize=(7.5, 4.2))
pts = [("C1 credit accuracy", sp["abstract.flip_share_C1"], sp["table1.C1_95CI_flip"]),
       ("C3 directional modal", sp["abstract.flip_share_C3"], sp["table1.C3_95CI_flip"])]
for i, (lab, pt, ci) in enumerate(pts):
    ax.errorbar(pt, i, xerr=[[pt - ci[0]], [ci[1] - pt]], fmt="o", ms=11, capsize=6, color="#1b3a6b")
    ax.text(pt, i + 0.14, f"{pt*100:.0f}%  [{ci[0]*100:.0f},{ci[1]*100:.0f}]", ha="center", fontsize=10)
ax.set_yticks([0, 1]); ax.set_yticklabels([p[0] for p in pts]); ax.set_xlim(0, 0.9); ax.set_ylim(-0.5, 1.6)
ax.set_xlabel("conclusion-flip share across specifications (95% bootstrap CI over items)")
ax.set_title("T1 · Conclusions flip across the specification space (perm p=%.3f)" % sp["table1.permutation_C1_p"])
fig.savefig(E / "T1_flip_shares.png"); plt.close(fig)

# ---------- T2 variance decomposition ----------
order = ["item", "residual_seed_noise", "provider_x_item", "A7_presentation", "A6_fewshot",
         "A1_provider", "A4_paraphrase", "A2_version", "A5_format", "A3_temperature"]
wcsv("T2_variance_decomposition.csv", ["component", "variance_share_pct"], [[k, var.get(k)] for k in order])
axc = [k for k in order if k not in ("item", "residual_seed_noise")]
fig, ax = plt.subplots(figsize=(8.5, 4.6))
b = ax.bar(range(len(axc)), [var[k] for k in axc], color="#3b6ea5")
ax.axhline(var["residual_seed_noise"], color="#b3202c", ls="--", lw=1.6,
           label=f"seed-noise floor = {var['residual_seed_noise']:.0f}%")
ax.set_xticks(range(len(axc))); ax.set_xticklabels([k.replace("_", "\n") for k in axc], fontsize=8.5)
ax.set_ylabel("variance share of credit letter-rank (%)")
ax.set_title(f"T2 · No design axis clears the noise floor (item alone = {var['item']:.0f}%)")
for bar, k in zip(b, axc):
    ax.text(bar.get_x() + bar.get_width()/2, var[k] + 0.1, f"{var[k]:.1f}", ha="center", fontsize=8)
ax.legend(); fig.savefig(E / "T2_variance_decomposition.png"); plt.close(fig)

# ---------- T3 vendor agreement ----------
wcsv("T3_vendor_agreement.csv", ["comparison", "band_agreement", "letter_agreement"], [
    ["within_family(same vendor, seeds)", ven["table3.within_family_agreement_band"], ven["table3.within_family_agreement_letter"]],
    ["cross_family(different vendors)", ven["table3.cross_family_agreement_band"], ven["table3.cross_family_agreement_letter"]],
    ["provider_main_effect_varshare_pct", var["A1_provider"], ""],
    ["provider_x_item_varshare_pct", var["provider_x_item"], ""]])
fig, ax = plt.subplots(figsize=(7.5, 4.4))
x = np.arange(2); w = 0.36
ax.bar(x - w/2, [ven["table3.within_family_agreement_band"], ven["table3.cross_family_agreement_band"]], w, label="band", color="#1565C0")
ax.bar(x + w/2, [ven["table3.within_family_agreement_letter"], ven["table3.cross_family_agreement_letter"]], w, label="letter", color="#EF6C00")
ax.set_xticks(x); ax.set_xticklabels(["within-vendor\n(seeds)", "cross-vendor"]); ax.set_ylim(0, 1)
ax.set_ylabel("decision agreement on identical items")
ax.set_title("T3 · Vendors agree less across than within — provider is interaction, not level\n"
             f"(provider main effect {var['A1_provider']:.1f}% vs provider×item {var['provider_x_item']:.1f}%)")
ax.legend(); fig.savefig(E / "T3_vendor_agreement.png"); plt.close(fig)

# ---------- T4 economic translation ----------
wcsv("T4_economic_translation.csv", ["metric", "value", "unit", "source"], [
    ["PRIMARY_percomparison_ighy_flip", eco["table4.PRIMARY_percomparison_ighy_flip"], "prob two random draws cross IG/HY", "primary, non-accumulating"],
    ["draws_per_name", eco["table4.draws_per_name"], "spec x seed draws per name", ""],
    ["ig_hy_crossing_MAXoverDraws", eco["table4.ig_hy_crossing_pct"], f"pct of names (n={eco['table4.ig_hy_denominator']}); union over ~{eco['table4.draws_per_name']} draws", "Altman Z''->rating->IG/HY"],
    ["mean_within_name_spread_range", eco["table4.mean_within_name_spread_range_bps"], "bps", "rating-spread map + Cornaggia anchor"],
    ["max_within_name_spread_range", eco["table4.max_within_name_spread_range_bps"], "bps", ""],
    ["cornaggia_anchor", 0, "note", eco["table4.cornaggia_anchor"]],
    ["implied_turnover_meanposdev", eco["table4.implied_turnover_meanposdev"], "position units", "directional modal churn"]])
fig, axs = plt.subplots(1, 2, figsize=(11, 4.3))
axs[0].bar(["straddle IG/HY", "stays one side"], [eco["table4.ig_hy_crossing_pct"], 100 - eco["table4.ig_hy_crossing_pct"]],
           color=["#8b1a1a", "#9e9e9e"]); axs[0].set_ylabel("% of names")
axs[0].set_title(f"T4a · {eco['table4.ig_hy_crossing_pct']:.0f}% of names get BOTH an\nIG and HY verdict (n={eco['table4.ig_hy_denominator']})")
axs[1].bar(["mean range", "max range"], [eco["table4.mean_within_name_spread_range_bps"], eco["table4.max_within_name_spread_range_bps"]], color="#4527A0")
axs[1].set_ylabel("implied spread range (bps)"); axs[1].set_title("T4b · Spec choice moves implied spread\n(rating-spread map; Cornaggia anchor)")
fig.savefig(E / "T4_economic_translation.png"); plt.close(fig)

# ---------- T5 granularity stability (NEW headline) ----------
agr = gr["table5.agreement_by_granularity"]; order_g = ["letter", "notch", "band", "ig_hy"]
cc = gr["table5.chance_corrected_POSTHOC"]
wcsv("T5_granularity_stability.csv",
     ["granularity", "n_cat", "raw_agreement", "chance_Pe", "fleiss_kappa", "gwet_ac1", "flip_prob"],
     [[g, cc[g]["n_categories"], cc[g]["raw_agreement"], cc[g]["chance_Pe_fleiss"], cc[g]["fleiss_kappa"],
       cc[g]["gwet_ac1"], gr["table5.flip_prob_by_granularity"][g]] for g in order_g] + [
    ["effective_resolution_raw90", gr["table5.effective_resolution_90pct"], "", "", "", "", ""],
    ["effective_resolution_kappa0.6", gr["table5.effective_resolution_kappa0.6"], "", "", "", "", ""],
    ["scale_usage_letters", gr["table5.scale_usage_letters"], "of 21", "", "", "", ""],
    ["scale_usage_entropy_bits", gr["table5.scale_usage_entropy_bits"], f"max {gr['table5.scale_max_entropy_bits']}", "", "", "", ""]])

# ---------- F1 spec curve C1 ----------
c1 = sorted(SC["C1"].values())
fig, ax = plt.subplots(figsize=(7.5, 4.4))
ax.plot(range(len(c1)), c1, "o-", color="#1b3a6b", ms=5); ax.axhline(0.5, color="#b3202c", ls="--", lw=1.2, label="majority threshold")
ax.set_xlabel("specification (sorted)"); ax.set_ylabel("band-level credit accuracy")
ax.set_title("F1 · Specification curve — credit accuracy (C1), 90-item battery"); ax.legend()
fig.savefig(E / "F1_spec_curve_C1.png"); plt.close(fig)

# ---------- F2 spec curve C3 ----------
from collections import Counter
c3 = Counter(SC["C3"].values())
fig, ax = plt.subplots(figsize=(6.5, 4.4))
ax.bar(["BUY", "HOLD", "SELL"], [c3.get(k, 0) for k in ["BUY", "HOLD", "SELL"]], color=["#2e7d32", "#757575", "#b71c1c"])
ax.set_ylabel("# specifications"); ax.set_title(f"F2 · Modal buy/hold/sell (C3) flips in {sp['abstract.flip_share_C3']*100:.0f}% of specs")
fig.savefig(E / "F2_spec_curve_C3.png"); plt.close(fig)

# ---------- F3 variance pareto ----------
fig, ax = plt.subplots(figsize=(8.5, 4.6))
b = ax.bar(range(len(axc)), [var[k] for k in axc], color="#3b6ea5")
ax.axhline(var["residual_seed_noise"], color="#b3202c", ls="--", lw=1.6, label=f"seed noise {var['residual_seed_noise']:.0f}%")
ax.set_xticks(range(len(axc))); ax.set_xticklabels([k.replace("_", "\n") for k in axc], fontsize=8.5)
ax.set_ylabel("variance share (%)"); ax.set_title("F3 · Variance Pareto (design axes vs noise floor)"); ax.legend()
fig.savefig(E / "F3_variance_pareto.png"); plt.close(fig)

# ---------- F4 deterministic subgrid ----------
fig, ax = plt.subplots(figsize=(7.5, 4.4))
r = det["table_det.band_accuracy_range"]
ax.bar(["min spec", "max spec"], r, color="#1b3a6b"); ax.axhline(0.5, color="#b3202c", ls="--", lw=1.2)
ax.set_ylabel("band accuracy (Google@temp0)")
ax.set_title(f"F4 · Fragility survives determinism — Google@temp0\naccuracy {r[0]:.2f}–{r[1]:.2f}, perm p={det['table_det.permutation_p']}")
fig.savefig(E / "F4_deterministic_subgrid.png"); plt.close(fig)

# ---------- F5 noise floor by provider ----------
mat = nz["table2.noise_matrix"]
labs = [f"{m['provider']}\nT{m['requested_temp']}" for m in mat]
vals = [m["seed_disagree"] or 0 for m in mat]
cols = ["#2E7D32" if m["temp_applied"] else "#C62828" for m in mat]
fig, ax = plt.subplots(figsize=(9.5, 4.4))
ax.bar(range(len(mat)), vals, color=cols); ax.set_xticks(range(len(mat))); ax.set_xticklabels(labs, fontsize=8)
ax.set_ylabel("seed-to-seed disagreement")
ax.set_title("F5 · Noise floor by provider × temperature (green=temp honored, red=dropped)")
fig.savefig(E / "F5_noise_floor_by_provider.png"); plt.close(fig)

# ---------- F6 granularity curve (NEW) — raw vs chance-corrected ----------
fig, ax = plt.subplots(figsize=(8.2, 4.8))
xs = order_g; ys = [agr[g] for g in xs]; ks = [cc[g]["fleiss_kappa"] for g in xs]
ax.plot(range(len(xs)), ys, "o-", color="#6a1b9a", ms=9, lw=2, label="raw agreement")
ax.plot(range(len(xs)), ks, "s--", color="#00695c", ms=8, lw=2, label="chance-corrected (Fleiss κ)")
for i in range(len(xs)):
    ax.text(i, ys[i] + 0.025, f"{ys[i]*100:.0f}%", ha="center", fontsize=9, color="#6a1b9a")
    ax.text(i, ks[i] - 0.055, f"κ={ks[i]:.2f}", ha="center", fontsize=9, color="#00695c")
ax.axhline(0.6, color="#b3202c", ls=":", lw=1, alpha=0.7); ax.text(3.05, 0.6, "κ=0.6\n(substantial)", color="#b3202c", fontsize=7.5)
ax.axhline(0.8, color="#999", ls=":", lw=1, alpha=0.6); ax.text(3.05, 0.8, "80% raw", color="#999", fontsize=7.5)
ax.set_xticks(range(len(xs))); ax.set_xticklabels(["letter\n(21)", "notch\n(9)", "band\n(3)", "IG/HY\n(2)"])
ax.set_ylim(0, 1); ax.set_ylabel("cross-specification agreement")
ax.set_title("F6 · Effective resolution — raw agreement rises with coarsening,\n"
             "but chance-corrected κ stays ≤0.46: no stable resolution, even binary IG/HY")
ax.legend(loc="center left"); fig.savefig(E / "F6_granularity_curve.png"); plt.close(fig)

# ---------- T6 human benchmark (POST-HOC) ----------
t6 = ADD["T6_human_benchmark"]["T6.rows"]
wcsv("T6_human_benchmark.csv",
     ["granularity", "machine_disagree", "human_split", "human_N", "z_naive", "p_naive", "p_dependence_adj", "conclusion"],
     [[r["granularity"], r["machine_percomparison_disagree"], r.get("human_split", ""), r.get("human_N", ""),
       r.get("z_naive", ""), r.get("p_naive", ""), r.get("p_dependence_adjusted", ""),
       r.get("conclusion", r.get("note", ""))] for r in t6])
tested = [r for r in t6 if r.get("human_split") is not None]
AGL = {"letter": "agency NOTCH\n(AA+ vs AA)\n= our 21-grade letter", "notch": "agency LETTER\n(AA vs A)\n= our 9-grade notch"}
fig, ax = plt.subplots(figsize=(8.2, 4.8))
x = np.arange(len(tested)); w = 0.38
ax.bar(x - w/2, [r["machine_percomparison_disagree"] for r in tested], w, label="machine (specifications)", color="#6a1b9a")
ax.bar(x + w/2, [r["human_split"] for r in tested], w, label="human agencies (Moody's/S&P split)", color="#2e7d32")
for i, r in enumerate(tested):
    ax.text(i - w/2, r["machine_percomparison_disagree"] + 0.02, f"{r['machine_percomparison_disagree']*100:.0f}%", ha="center", fontsize=10, fontweight="bold")
    ax.text(i + w/2, r["human_split"] + 0.02, f"{r['human_split']*100:.0f}%", ha="center", fontsize=10)
    ax.text(i, max(r["machine_percomparison_disagree"], r["human_split"]) + 0.12, f"z={r['z_naive']:.0f}, p{r['p_dependence_adjusted']}", ha="center", fontsize=8.5, color="#b3202c")
ax.set_xticks(x); ax.set_xticklabels([AGL[r["granularity"]] for r in tested], fontsize=8.5); ax.set_ylim(0, 1.05)
ax.set_ylabel("per-comparison disagreement / split rate")
ax.set_title("T6 · Machine specification-disagreement EXCEEDS human agency splits\n(LIKE-FOR-LIKE by agency scale; item-clustered bootstrap; Livingston et al. N=13,853)")
ax.legend(loc="center right"); fig.savefig(E / "T6_human_benchmark.png"); plt.close(fig)

# ---------- T4 market-priced upgrade (POST-HOC) ----------
mp = MKT
wcsv("T4_market_priced.csv", ["metric", "value_bps", "note"], [
    ["per_name_spread_range_median", mp["economic.market_priced.per_name_spread_range_median_bps"], f"median across {mp['economic.market_priced.n_names']} names, over {mp['economic.market_priced.n_trading_days']} trading days"],
    ["per_name_spread_range_IQR_low", mp["economic.market_priced.per_name_spread_range_IQR_bps"][0], ""],
    ["per_name_spread_range_IQR_high", mp["economic.market_priced.per_name_spread_range_IQR_bps"][1], ""],
    ["floor_never_below_any_day", mp["economic.market_priced.floor_any_name_any_day_bps"], "min across all names & trading days"],
    ["median_name_floor", mp["economic.market_priced.median_name_floor_bps"], ""],
    ["share_verdict_reaches_CCC", mp["economic.market_priced.share_verdict_reaches_CCC"], "SATURATION: these names pin median at the CCC-AAA ceiling (fragility stat itself)"],
    ["nonsaturating_median", mp["economic.market_priced.nonsaturating_spread_range_median_IQR_bps"][0], f"n={mp['economic.market_priced.n_nonsaturating']} names not reaching CCC; IQR {mp['economic.market_priced.nonsaturating_spread_range_median_IQR_bps'][1:]}"],
    ["cornaggia_literature_anchor", "80-140", "per 2-3 notches (retained alongside)"]])
pn = mp["_per_name"]; meds = sorted(v["median_bps"] for v in pn.values())
fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.4))
axs[0].hist(meds, bins=15, color="#4527A0", edgecolor="white")
axs[0].axvline(mp["economic.market_priced.per_name_spread_range_median_bps"], color="#b3202c", ls="--", lw=1.5,
               label=f"median {mp['economic.market_priced.per_name_spread_range_median_bps']:.0f} bps")
axs[0].set_xlabel("per-name implied spread range (bps, median across days)"); axs[0].set_ylabel("# names")
axs[0].set_title("T4-market · Market-priced spread range per name\n(ICE BofA OAS, FRED, 2023-2026)"); axs[0].legend()
floors = sorted(v["min_bps"] for v in pn.values())
axs[1].hist(floors, bins=15, color="#00695c", edgecolor="white")
axs[1].axvline(mp["economic.market_priced.floor_any_name_any_day_bps"], color="#b3202c", ls="--", lw=1.5,
               label=f"absolute floor {mp['economic.market_priced.floor_any_name_any_day_bps']:.0f} bps")
axs[1].set_xlabel("per-name floor (bps, min across trading days)"); axs[1].set_ylabel("# names")
axs[1].set_title("T4-market · Even on the tightest market day,\nranges stay wide"); axs[1].legend()
fig.savefig(E / "T4_market_priced.png"); plt.close(fig)

print("exhibits written:", sorted(p.name for p in E.glob("T*.csv")) + sorted(p.name for p in E.glob("*.png")))
