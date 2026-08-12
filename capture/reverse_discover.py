#!/usr/bin/env python3
"""Appendix D — REVERSE discovery (run LOCALLY, keyless).

Instead of screening mid-caps and hoping they disclose a rating, this searches SEC EDGAR full-text
for the 10-Ks that DO print an agency rating token, and keeps the non-financial issuers. This
directly finds rating-disclosing issuers (esp. the scarce HY/DISTRESS names). Moody's notation is
used because it is unambiguous in full text (Ba2, B3, Caa1 don't collide with common words).

Output: discovered.json = [{ticker, cik, prelim_band, token, sic, accession, filing_date}]
No market-cap filter here (needs FMP). The assistant filters to mid-cap via its own connection next.

RUN:
    pip install requests
    python3 reverse_discover.py
"""
import re, json, time
from pathlib import Path
import requests

HERE = Path(__file__).resolve().parent
UA = "Samir Chincholikar samir.chincholikar@gmail.com"
S = requests.Session(); S.headers.update({"User-Agent": UA})
DATE_FROM, DATE_TO = "2024-07-01", "2025-12-31"   # ~last 12-18 months of 10-Ks

# Moody's notches -> band. ONLY unambiguous multi-char tokens (3+ char, or 2-char with a lowercase
# 'a' + digit). Single-letter tokens (A1/A2/A3/B1/B2/B3/Ca/C) are DROPPED — they collide with
# section labels ("Item 1A", "Note B2") and state abbreviations ("Ca"=California), producing
# thousands of false positives. We lose single-A (SAFE) and single-B (deep-HY) coverage, but Aa/Baa
# fill SAFE and Ba/Caa fill WATCH/DISTRESS; the downstream parser confirms every real rating anyway.
TOKENS = {
 # Moody's notches
 "Aaa":"SAFE","Aa1":"SAFE","Aa2":"SAFE","Aa3":"SAFE","Baa1":"SAFE","Baa2":"SAFE","Baa3":"SAFE",
 "Ba1":"WATCH","Ba2":"WATCH","Ba3":"WATCH",
 "Caa1":"DISTRESS","Caa2":"DISTRESS","Caa3":"DISTRESS",
 # S&P/Fitch SIGNED notches only (bare BBB/BB are too common in text). Finds issuers that disclose
 # an S&P/Fitch rating but not Moody's -> NEW names not in the Moody's-only pool.
 "BBB+":"SAFE","BBB-":"SAFE","BB+":"WATCH","BB-":"WATCH","CCC+":"DISTRESS","CCC-":"DISTRESS",
}
MAX_HITS_PER_TOKEN = 400   # bound pagination for common tokens

def efts(token, frm=0):
    url = ("https://efts.sec.gov/LATEST/search-index"
           f"?q=%22{token}%22&forms=10-K&startdt={DATE_FROM}&enddt={DATE_TO}&from={frm}")
    for _ in range(4):
        r = S.get(url, timeout=60)
        if r.status_code == 200 and r.text.strip():
            try: return r.json()
            except Exception: pass
        time.sleep(1.5)
    return None

TICK = re.compile(r"\(([A-Z][A-Z.]{0,5})(?:,|\))")
def parse_hit(h):
    src = h["_source"]
    names = src.get("display_names", [])
    tick = None
    for nm in names:
        m = TICK.search(nm)
        if m: tick = m.group(1); break
    sics = src.get("sics", []); sic = int(sics[0]) if sics and str(sics[0]).isdigit() else 0
    return tick, int(src["ciks"][0]), sic, src["adsh"], src.get("file_date","")

def is_financial(sic):  # GICS Financials/Real Estate ~ SIC 6000-6799
    return 6000 <= sic <= 6799

def main():
    found = {}   # ticker -> record (keep the RISKIEST band seen, to prioritize HY/DISTRESS)
    bandrank = {"SAFE":0,"WATCH":1,"DISTRESS":2}
    for tok, band in TOKENS.items():
        frm = 0; total = None; got = 0
        while True:
            j = efts(tok, frm)
            if not j: break
            hits = j["hits"]["hits"]; total = j["hits"]["total"]["value"]
            for h in hits:
                tick, cik, sic, adsh, fdate = parse_hit(h)
                if not tick or is_financial(sic): continue
                rec = {"ticker":tick,"cik":cik,"prelim_band":band,"token":tok,"sic":sic,
                       "accession":adsh,"filing_date":fdate}
                if tick not in found or bandrank[band] > bandrank[found[tick]["prelim_band"]]:
                    found[tick] = rec
            got += len(hits)
            if got >= total or not hits or got >= MAX_HITS_PER_TOKEN: break
            frm += len(hits); time.sleep(0.3)
        print(f"  {tok:5s} band={band:8s} cum_issuers={len(found)}")
        time.sleep(0.3)
    recs = sorted(found.values(), key=lambda r:(-bandrank[r["prelim_band"]], r["ticker"]))
    json.dump({"n":len(recs),"date_window":[DATE_FROM,DATE_TO],
               "note":"Non-financial issuers whose recent 10-K prints a Moody's rating token. prelim_band from the token; confirmed later by the parser. No market-cap filter yet.",
               "issuers":recs}, open(HERE/"discovered.json","w"), indent=1)
    import collections
    print(f"\nDISCOVERED {len(recs)} rating-disclosing non-financial issuers -> discovered.json")
    print("prelim band mix:", dict(collections.Counter(r["prelim_band"] for r in recs)))
    print("HY/DISTRESS tickers:", [r["ticker"] for r in recs if r["prelim_band"]!="SAFE"][:80])

if __name__ == "__main__":
    main()
