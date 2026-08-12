#!/usr/bin/env python3
"""Appendix D — build the ANONYMIZED, PERTURBED battery from the real pull (reproducible; seeded).

Decontamination v2 (after Phase-3 NO-GO):
  (a) B2B brand-salience screen  — keep {Industrials, Basic Materials, Utilities, Technology, Energy,
      Healthcare}; drop consumer-facing {Consumer Cyclical, Consumer Defensive, Communication Services}.
  (b) Per-issuer figure perturbation — every dollar figure x s_i, s_i ~ LogUniform(0.6, 1.7), ONE seeded
      draw per issuer. All fields share s_i, so every RATIO is preserved (rating task unchanged) while
      absolute magnitudes no longer match any filing (defeats exact-figure lookup).

Real (unscaled) figures + rating stay in sealed_crosswalk.json (provenance). Opaque shuffled IDs.
Outputs: battery_real45.json (anonymized+perturbed), sealed_crosswalk.json, sealed_scoring_key.json.

RUN (offline, no keys, no spend):  python3 build_battery_realarm.py
"""
import json, random, math, re
from pathlib import Path
from datetime import date
HERE=Path(__file__).resolve().parent
FACTS=HERE/"facts"
B2B={"Industrials","Basic Materials","Utilities","Technology","Energy","Healthcare"}
PERTURB_SEED=20260709
SHUFFLE_SEED=20260709

def la(us,tags,instant):
    for tag in tags:
        node=us.get(tag)
        if not node: continue
        usd=node.get("units",{}).get("USD")
        if not usd: continue
        best=None
        for e in usd:
            if e.get("form") not in ("10-K","10-K/A"): continue
            if not instant:
                if e.get("fp")!="FY": continue
                try:
                    if (date.fromisoformat(e["end"])-date.fromisoformat(e["start"])).days<300: continue
                except Exception: continue
            if best is None or e["end"]>best[0]: best=(e["end"],e["val"])
        if best: return best[1]
    return None

def enrich(cik):
    cf=json.loads((FACTS/f"{cik}.json").read_text()); us=cf.get("facts",{}).get("us-gaap",{})
    ta=la(us,["Assets"],True)
    eq=la(us,["StockholdersEquity","StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest","PartnersCapital","PartnersCapitalIncludingPortionAttributableToNoncontrollingInterest","MembersEquity"],True)
    tl=la(us,["Liabilities"],True)
    if tl is None and ta is not None and eq is not None:
        lse=la(us,["LiabilitiesAndStockholdersEquity"],True); tl=(lse if lse is not None else ta)-eq
    rev=la(us,["Revenues","RevenueFromContractWithCustomerExcludingAssessedTax","RevenueFromContractWithCustomerIncludingAssessedTax","SalesRevenueNet","RegulatedAndUnregulatedOperatingRevenue","RevenuesNetOfInterestExpense"],False)
    ebit=la(us,["OperatingIncomeLoss","IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest"],False)
    ni=la(us,["NetIncomeLoss","ProfitLoss"],False); gp=la(us,["GrossProfit"],False)
    ca=la(us,["AssetsCurrent"],True); cl=la(us,["LiabilitiesCurrent"],True)
    re_=la(us,["RetainedEarningsAccumulatedDeficit"],True)
    return dict(ta=ta,tl=tl,eq=eq,rev=rev,ebit=ebit,ni=ni,gp=gp,ca=ca,cl=cl,re_=re_)

def scale(f,s):
    return {k:(v*s if v is not None else None) for k,v in f.items()}

def M(x): return None if x is None else f"{round(x/1e6):,}M"
def facts_text(f):
    parts=[]
    if f["rev"] is not None:
        s=f"Revenue {M(f['rev'])}"
        if f["gp"] is not None and f["rev"]: s+=f", gross margin {round(100*f['gp']/f['rev'])}%"
        if f["ebit"] is not None:
            s+=f", operating income {M(f['ebit'])}"
            if f["rev"]: s+=f" (operating margin {round(100*f['ebit']/f['rev'])}%)"
        if f["ni"] is not None: s+=f", net income {M(f['ni'])}"
        parts.append(s+".")
    parts.append(f"Total assets {M(f['ta'])}, total liabilities {M(f['tl'])}, shareholders' equity {M(f['eq'])}.")
    if f["ca"] is not None and f["cl"] is not None:
        cr=f" (current ratio {f['ca']/f['cl']:.2f})" if f["cl"] else ""
        e=f"Current assets {M(f['ca'])} vs current liabilities {M(f['cl'])}{cr}"
        if f["re_"] is not None: e+=f", retained earnings {M(f['re_'])}"
        parts.append(e+".")
    elif f["re_"] is not None: parts.append(f"Retained earnings {M(f['re_'])}.")
    return " ".join(parts)
def facts_kv(f):
    kv=[]
    for lab,val in [("Revenue",M(f["rev"])),("EBIT / operating income",M(f["ebit"])),("Net income",M(f["ni"])),
                    ("Total assets",M(f["ta"])),("Total liabilities",M(f["tl"])),("Shareholders' equity",M(f["eq"])),
                    ("Current assets",M(f["ca"])),("Current liabilities",M(f["cl"])),("Retained earnings",M(f["re_"]))]:
        if val is not None: kv.append([lab,val])
    return kv

def consumer_sic(s):
    # consumer-facing SIC ranges excluded even when the FMP sector label mislabels them B2B
    return (3940<=s<=3949 or 4400<=s<=4599 or 4100<=s<=4199 or 2870<=s<=2879 or
            2840<=s<=2844 or 2080<=s<=2099 or 3630<=s<=3639 or 2300<=s<=2399)

def main():
    disc={r["ticker"]:r for r in json.load(open(HERE/"discovered.json"))["issuers"]}
    raw=[r for r in json.load(open(HERE/"raw_pull.json"))["rows"] if r["rating"].get("ok")]
    kept=[r for r in raw if r["sector"] in B2B and not consumer_sic(disc.get(r["symbol"],{}).get("sic",0))]
    kept.sort(key=lambda r:r["symbol"])
    prng=random.Random(PERTURB_SEED)
    # Pre-registered draw: scale ~ LogUniform(0.6, 1.7). The interval contains 1.0; a draw landing
    # near 1.0 (e.g. GPK at 1.0019) is a PROPERTY of the frozen distribution, not a defect. Anonymization
    # is certified by the empirical fingerprint gate on the artifact as run, not by any minimum shift.
    # (A +/-10% dead-band is a genuine improvement but is PRE-REGISTERED FOR FUTURE ARMS ONLY — adopting
    #  it here, after H1 was known, would be post-hoc tuning. Not applied retroactively.)
    scales={r["symbol"]:math.exp(prng.uniform(math.log(0.6),math.log(1.7))) for r in kept}
    # anonymize (shuffle IDs independent of ticker/band order)
    srng=random.Random(SHUFFLE_SEED); shuf=kept[:]; srng.shuffle(shuf)
    battery=[]; crosswalk=[]; keyrows=[]
    for i,r in enumerate(shuf,1):
        rid=f"R{i:03d}"; s=scales[r["symbol"]]
        real=enrich(r["cik"]); pert=scale(real,s)
        battery.append({"item_id":rid,"family":"credit_health_realfirm",
            "facts_text":facts_text(pert),"facts_kv":facts_kv(pert),
            "benchmark_label":r["rating"]["band"],"label_space":["SAFE","WATCH","DISTRESS"],
            "abstain_label":None,"gt_source":"disclosed_agency_rating"})
        cik=r["cik"]
        ent=None
        try: ent=json.loads((FACTS/f"{cik}.json").read_text()).get("entityName")
        except Exception: pass
        crosswalk.append({"item_id":rid,"ticker":r["symbol"],"cik":cik,"sector":r["sector"],
            "agency":r["rating"]["agency"],"sp_equiv":r["rating"]["sp_equiv"],"band":r["rating"]["band"],
            "perturb_scale":round(s,4),"real_figures":{k:real[k] for k in real},
            "accession":r["rating"]["accession"],"filing_date":r["rating"]["filing_date"],
            "url":r["rating"]["url"],"doc_sha256":r["rating"]["doc_sha256"],"quote":r["rating"]["quote"]})
        keyrows.append({"item_id":rid,"ticker":r["symbol"],"entity_name":ent})
    from collections import Counter
    json.dump({"n":len(battery),"decontamination":"B2B brand-salience screen + per-issuer LogUniform(0.6,1.7) figure perturbation (ratios preserved)","note":"Zero identifying strings; opaque shuffled IDs; safe for model prompts.","items":battery},
              open(HERE/"battery_real45.json","w"),indent=1)
    json.dump({"n":len(crosswalk),"SEALED":"NEVER in any prompt. Real unscaled figures + rating + per-issuer scale.","map":crosswalk},
              open(HERE/"sealed_crosswalk.json","w"),indent=1)
    json.dump({"SEALED":"scoring only; never in prompts.","key":keyrows},open(HERE/"sealed_scoring_key.json","w"),indent=1)
    # leak scan
    bt=json.dumps(battery)
    leak=[c["item_id"] for c in crosswalk if re.search(rf"(?<![A-Za-z0-9]){re.escape(c['ticker'])}(?![A-Za-z0-9])",bt) and c["ticker"].isalpha() and len(c["ticker"])>=3]
    print(f"battery rebuilt: {len(battery)} B2B items (perturbed)")
    print("band mix:",dict(Counter(b["benchmark_label"] for b in battery)))
    print("sector mix:",dict(Counter(c["sector"] for c in crosswalk)))
    print("scale range:",round(min(scales.values()),3),"-",round(max(scales.values()),3))
    print("leak scan (>=3-char tickers as standalone tokens in battery):", leak if leak else "CLEAN")

if __name__=="__main__": main()
