#!/usr/bin/env python3
"""Appendix D — Real-firm arm PHASE 1 collector (LOCAL, fully self-sufficient, keyless).

Reads candidates.json (reverse-discovered US mid-cap $2-15B rating-disclosing issuers). For each,
pulls its own fundamentals from SEC XBRL companyfacts and its agency rating from the latest 10-K,
both from free SEC endpoints (only a User-Agent needed). Walks the whole pool in ticker order,
SKIPPING any that don't fit (fundamentals incomplete, or no real disclosed issuer rating), and
STOPS when it has N_TARGET that pass. No FMP, no API key.

RUN:  pip install requests beautifulsoup4 lxml ; python3 realarm_collect.py
"""
from __future__ import annotations
import re, json, time, hashlib, html, sys, csv
from pathlib import Path
from datetime import datetime, date, timezone
import requests
from bs4 import BeautifulSoup

HERE=Path(__file__).resolve().parent
CACHE=HERE/"cache"; CACHE.mkdir(exist_ok=True); RAW=HERE/"raw"; RAW.mkdir(exist_ok=True)
FACTS=HERE/"facts"; FACTS.mkdir(exist_ok=True)
USER_AGENT="Samir Chincholikar samir.chincholikar@gmail.com"
N_TARGET, N_RESERVE = 50, 15
SECTOR_CAP = 10
MAX_10K_AGE_DAYS = 500
SEC_RPS = 6

_s=requests.Session(); _s.headers.update({"User-Agent":USER_AGENT}); _last=[0.0]
def sec_get(url):
    dt=time.time()-_last[0]
    if dt<1.0/SEC_RPS: time.sleep(1.0/SEC_RPS-dt)
    r=_s.get(url,timeout=90); _last[0]=time.time(); return r

# ---------- fundamentals from SEC XBRL companyfacts ----------
def companyfacts(cik):
    p=FACTS/f"{cik}.json"
    if p.exists():
        try: return json.loads(p.read_text())
        except Exception: pass
    r=sec_get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json")
    if r.status_code!=200: return None
    p.write_bytes(r.content);
    try: return r.json()
    except Exception: return None

def latest_annual(us, tags, instant):
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
            if best is None or e["end"]>best[0]: best=(e["end"], e["val"])
        if best: return best[1]
    return None

def fundamentals(cik):
    cf=companyfacts(cik)
    if not cf: return None
    us=cf.get("facts",{}).get("us-gaap",{})
    ta=latest_annual(us,["Assets"],True)
    tl=latest_annual(us,["Liabilities"],True)
    eq=latest_annual(us,["StockholdersEquity","StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
                         "PartnersCapital","PartnersCapitalIncludingPortionAttributableToNoncontrollingInterest",
                         "MembersEquity","MembersEquityIncludingPortionAttributableToNoncontrollingInterest"],True)
    # Many issuers report LiabilitiesAndStockholdersEquity (=total assets) but no standalone
    # `Liabilities` tag. Recover total liabilities via the balance-sheet identity L = A - Equity.
    if tl is None and ta is not None and eq is not None:
        lse=latest_annual(us,["LiabilitiesAndStockholdersEquity"],True)
        base=lse if lse is not None else ta
        tl=base-eq
    ebit=latest_annual(us,["OperatingIncomeLoss","IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest","IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"],False)
    rev=latest_annual(us,["Revenues","RevenueFromContractWithCustomerExcludingAssessedTax","RevenueFromContractWithCustomerIncludingAssessedTax","SalesRevenueNet","RegulatedAndUnregulatedOperatingRevenue","RevenuesNetOfInterestExpense"],False)
    # CORE fields (universally reported) are required; utilities file UNCLASSIFIED balance sheets
    # (no current split) so working capital / retained earnings are OPTIONAL. Z'' is computed only
    # when the classified figures exist; the agency rating (not Z'') is the arm's benchmark.
    if None in (ta,tl,eq,ebit,rev) or ta==0 or tl==0: return None
    ca=latest_annual(us,["AssetsCurrent"],True)
    cl=latest_annual(us,["LiabilitiesCurrent"],True)
    re_=latest_annual(us,["RetainedEarningsAccumulatedDeficit"],True)
    wc=(ca-cl) if (ca is not None and cl is not None) else None
    z=(6.56*(wc/ta)+3.26*((re_ or 0)/ta)+6.72*(ebit/ta)+1.05*(eq/tl)) if (wc is not None and re_ is not None) else None
    zb=("SAFE" if z>2.60 else "DISTRESS" if z<1.10 else "WATCH") if z is not None else "n/a"
    return {"totalAssets":ta,"totalLiabilities":tl,"equity":eq,"retainedEarnings":re_,
            "workingCapital":wc,"ebit":ebit,"revenue":rev,"altmanZScore":z,"z_band":zb}

# ---------- rating extraction (precision-guarded; validated) ----------
MOODY=r"(?:Aaa|Aa[123]|A[123]|Baa[123]|Ba[123]|B[123]|Caa[123]|Ca|C)"
SPF=r"(?:AAA|AA[+-]?|A[+-]?|BBB[+-]?|BB[+-]?|B[+-]?|CCC[+-]?|CC|C|D)"
MO2SP={"Aaa":"AAA","Aa1":"AA+","Aa2":"AA","Aa3":"AA-","A1":"A+","A2":"A","A3":"A-","Baa1":"BBB+","Baa2":"BBB","Baa3":"BBB-","Ba1":"BB+","Ba2":"BB","Ba3":"BB-","B1":"B+","B2":"B","B3":"B-","Caa1":"CCC+","Caa2":"CCC","Caa3":"CCC-","Ca":"CC","C":"C"}
ORDER=["AAA","AA+","AA","AA-","A+","A","A-","BBB+","BBB","BBB-","BB+","BB","BB-","B+","B","B-","CCC+","CCC","CCC-","CC","C","D"]
def rating_to_band(sp):
    i=ORDER.index(sp); return "SAFE" if i<=ORDER.index("BBB-") else "WATCH" if i<=ORDER.index("B-") else "DISTRESS"
NEG=("performance graph","cumulative total","total shareholder return","total return","peer group","russell","s&p 500","s&p 400","s&p midcap","poor's 500","poor's 400","invested $","$100 invested","$100 on","$100 in","class a common","class b common","stock performance","index (b)","(b)(c)","minimum credit rating","minimum rating","minimum long-term","counterpart","institutions with","if downgraded","were downgraded","would be downgraded","is downgraded","are downgraded","should we be downgraded","fall below","falls below","collateral if","rated at least","surplus cash","money market","treasury note","treasury bond","government agency bond","invest in securities","securities rated","must be rated","securities with original maturities","maturities of greater","maturities of less","interest-bearing","cash equivalents","marketable securities","investment policy","held-to-maturity","corporate bond","commercial paper","provide collateral","secure the facility","facility should","credit facility contains","facility contains provisions")
POS=("our credit rating","our corporate","our issuer","our senior","our long-term","our debt","our notes","company's credit rating","company's senior","company's long-term","credit ratings are","credit rating is","rated ","rating of ","ratings of ","affirmed","reaffirmed","assigned a","corporate family rating","issuer credit rating","senior unsecured","long-term issuer","corporate credit rating","current ratings","ratings assigned","credit ratings remained","credit rating remained","downgraded our","upgraded our")
STRONG=("issuer credit rating","corporate credit rating","senior unsecured","corporate family","long-term issuer","issuer rating")
def extract_rating(text):
    AG=[("S&P",r"Standard\s*&\s*Poor'?’?s|S&P\s*Global|S&P",SPF,False),("Fitch",r"Fitch",SPF,False),("Moody's",r"Moody'?’?s",MOODY,True)]
    hits=[]
    for s in re.split(r"(?<=[.;])\s+",text):
        ctx=s.lower()
        if any(n in ctx for n in NEG): continue
        if not any(p in ctx for p in POS): continue
        for agency,name_pat,scale,is_moody in AG:
            tok=re.compile(rf"(?<![A-Za-z0-9])({scale})(?![A-Za-z0-9])")
            for m in re.finditer(name_pat,s,re.I):
                lo,hi=max(0,m.start()-80),min(len(s),m.end()+80); seg=s[lo:hi]; ap=m.start()-lo; segl=seg.lower()
                best=None; bd=1e9
                for tk in tok.finditer(seg):
                    raw=tk.group(1); sp=MO2SP.get(raw,raw) if is_moody else raw
                    if sp not in ORDER: continue
                    if raw in ("A","B","C","D","Ca") and not any(k in segl for k in STRONG): continue
                    d=min(abs(tk.start()-ap),abs(tk.end()-ap))
                    if d<bd: bd=d; best=(sp,raw)
                if not best: continue
                conf="high" if any(k in ctx for k in ("issuer","senior","unsecured","corporate family","corporate credit","long-term")) else "med"
                hits.append((agency,best[0],s.strip()[:400],conf))
    for pref in ("S&P","Moody's","Fitch"):
        cs=[h for h in hits if h[0]==pref]
        if cs: cs.sort(key=lambda h:0 if h[3]=="high" else 1); return cs[0][1],cs[0][0],cs[0][2],cs[0][3]
    return None
def latest_10k(cik):
    j=json.loads((CACHE/f"subm_{cik}.json").read_text()) if (CACHE/f"subm_{cik}.json").exists() else None
    if j is None:
        r=sec_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json"); (CACHE/f"subm_{cik}.json").write_bytes(r.content); j=r.json()
    rec=j["filings"]["recent"]
    for form,acc,doc,fd in zip(rec["form"],rec["accessionNumber"],rec["primaryDocument"],rec["filingDate"]):
        if form=="10-K":
            age=(datetime.now().date()-datetime.fromisoformat(fd).date()).days
            return {"accession":acc,"doc":doc,"filing_date":fd,"age_days":age,"url":f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-','')}/{doc}"}
    return None
def get_rating(cik):
    f=latest_10k(cik)
    if not f or f["age_days"]>MAX_10K_AGE_DAYS: return {"ok":False,"reason":"no_current_10k"}
    raw=RAW/f"{cik}_{f['accession']}.htm"
    if not raw.exists(): raw.write_bytes(sec_get(f["url"]).content)
    body=raw.read_bytes(); sha=hashlib.sha256(body).hexdigest()
    text=html.unescape(re.sub(r"\s+"," ",BeautifulSoup(body,"lxml").get_text(" ")))
    ext=extract_rating(text)
    if not ext: return {"ok":False,"reason":"rating_not_disclosed"}
    sp,agency,sent,conf=ext
    return {"ok":True,"sp_equiv":sp,"agency":agency,"band":rating_to_band(sp),"quote":sent[:400],"confidence":conf,
            "accession":f["accession"],"url":f["url"],"filing_date":f["filing_date"],"doc_sha256":sha,
            "retrieved_utc":datetime.now(timezone.utc).isoformat(),
            "efts_verify":f'https://efts.sec.gov/LATEST/search-index?q=%22{sp}%22&forms=10-K&ciks={cik:010d}'}

def main():
    cand=json.loads((HERE/"candidates.json").read_text())["candidates"]
    print(f"walking {len(cand)} candidates; target {N_TARGET} primary + {N_RESERVE} reserve\n")
    primary,reserve,raw_pull=[],[],[]; sect={}; nfund=nrate=0
    for i,c in enumerate(cand):
        if len(primary)>=N_TARGET and len(reserve)>=N_RESERVE: break
        sym,cik,sector=c["symbol"],c["cik"],c["sector"]
        fu=fundamentals(cik)
        if not fu: nfund+=1; print(f"  [{i+1:3d}] {sym:6s} skip (no XBRL fundamentals)"); continue
        rat=get_rating(cik)
        row={"symbol":sym,"cik":cik,"sector":sector,"marketCap":c["marketCap"],"altmanZ":fu["altmanZScore"],"z_band":fu["z_band"],"fundamentals":fu,"rating":rat}
        raw_pull.append(row)
        if not rat["ok"]: nrate+=1; print(f"  [{i+1:3d}] {sym:6s} skip ({rat['reason']})"); continue
        if sect.get(sector,0)>=SECTOR_CAP:
            dest="reserve" if len(reserve)<N_RESERVE else None
        elif len(primary)<N_TARGET: dest="primary"
        elif len(reserve)<N_RESERVE: dest="reserve"
        else: dest=None
        if dest=="primary": primary.append(row); sect[sector]=sect.get(sector,0)+1
        elif dest=="reserve": reserve.append(row)
        zs=f"{fu['altmanZScore']:5.2f}" if fu['altmanZScore'] is not None else "  n/a"
        print(f"  [{i+1:3d}] {sym:6s} {rat['sp_equiv']:>4s}({rat['agency'][:3]}) {rat['band'][:4]:4s} Z={zs} -> {dest or 'full'}  (primary {len(primary)}/{N_TARGET})")
    # freeze
    def dump(n,o): (HERE/n).write_text(json.dumps(o,indent=1))
    import collections
    bandmix=dict(collections.Counter(r["rating"]["band"] for r in primary))
    dump("raw_pull.json",{"pulled_utc":datetime.now(timezone.utc).isoformat(),"rows":raw_pull})
    dump("primary_set.json",{"n":len(primary),"band_mix":bandmix,"sector_counts":sect,"issuers":primary})
    dump("reserve_set.json",{"n":len(reserve),"issuers":reserve})
    with open(HERE/"ratings_provenance.csv","w",newline="") as fh:
        w=csv.writer(fh); w.writerow(["symbol","cik","agency","sp_equiv_rating","band","z_band","altmanZ","marketCap","confidence","accession","filing_date","doc_sha256","url","efts_verify","quote"])
        for r in primary+reserve:
            t=r["rating"]; zz=round(r["altmanZ"],3) if r["altmanZ"] is not None else ""
            w.writerow([r["symbol"],r["cik"],t["agency"],t["sp_equiv"],t["band"],r["z_band"],zz,r["marketCap"],t["confidence"],t["accession"],t["filing_date"],t["doc_sha256"],t["url"],t["efts_verify"],t["quote"]])
    files=["selection_rule.md","reverse_discover.py","discovered.json","candidates.json","raw_pull.json","primary_set.json","reserve_set.json","ratings_provenance.csv","realarm_collect.py"]
    h=hashlib.sha256()
    for fn in files:
        if (HERE/fn).exists(): h.update((HERE/fn).read_bytes())
    (HERE/"MANIFEST_REALARM.sha256").write_text(h.hexdigest()+"  "+", ".join(files)+"\n")
    print("\n=== FROZEN ===")
    print(f"PRIMARY {len(primary)}/{N_TARGET}  band {bandmix}  sectors {sect}")
    print(f"RESERVE {len(reserve)}/{N_RESERVE}   | MANIFEST_REALARM: {h.hexdigest()[:16]}")
    print(f"examined {len(raw_pull)} | skipped: {nfund} no-fundamentals, {nrate} rating-not-disclosed")
    if len(primary)<N_TARGET: print(f"NOTE: under {N_TARGET} — pool exhausted; ask assistant to widen candidates.json.")
    low=[r["symbol"] for r in primary if r["rating"]["confidence"]!="high"]
    if low: print(f"MANUAL-REVIEW (verify quote vs URL): {low}")

if __name__=="__main__": main()
