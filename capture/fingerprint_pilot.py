#!/usr/bin/env python3
"""Appendix D — Real-firm arm · PHASE 3 fingerprinting gate (LOCAL execution; the analysis
sandbox cannot reach provider APIs). First phase that spends money.

Probes memorization/contamination: shows each ANONYMIZED profile (battery_real45.json — opaque
IDs, zero identifying strings) to each pinned model and asks it to NAME the real company/ticker.
If a model can still name the firm from decontaminated figures, that firm is memorized. Scoring is
LOCAL against sealed_scoring_key.json (ticker + SEC entity name) — the key NEVER enters a prompt.

Grid: 45 items x {gpt-5.4-nano, gemini-3.5-flash} x 3 seeds = 270 calls. Resume-safe (one immutable
JSON per call). Hard cost stop at $20 (arm cap $150; expected ~$1.11).

GATE (pre-registered): per-item identification share  <5% GO | 5-15% RE-TEST | >15% NO-GO.

RUN:
  cd appendixD_realarm
  python3 fingerprint_pilot.py            # keys auto-load from ../../API Keys/keys.env.txt
  # offline dry-run (no keys, no spend):  PILOT_MOCK=1 python3 fingerprint_pilot.py
"""
from __future__ import annotations
import os, json, time, hashlib, re, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
MOCK=os.environ.get("PILOT_MOCK")=="1"

# ---- run isolation: each run gets its own timestamped folder; old runs are NEVER touched.
# Resume-safe WITHIN a run: a crash-restart continues the same run (via .active_run pointer)
# instead of starting a new one. Force a brand-new run with FP_NEW_RUN=1; pin one with FP_RUN_ID.
RUNS=HERE/"fp_runs"; RUNS.mkdir(exist_ok=True)
_ACTIVE=RUNS/".active_run"
if MOCK:
    RUN_ID="mock"
elif os.environ.get("FP_RUN_ID"):
    RUN_ID=os.environ["FP_RUN_ID"]
elif _ACTIVE.exists() and os.environ.get("FP_NEW_RUN")!="1":
    RUN_ID=_ACTIVE.read_text().strip()
else:
    RUN_ID=datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR=RUNS/("run_mock" if MOCK else f"run_{RUN_ID}")
RAW=RUN_DIR/"raw"; RAW.mkdir(parents=True,exist_ok=True)
if not MOCK: _ACTIVE.write_text(RUN_ID)
RESULT_PATH=RUN_DIR/"fingerprint_result.json"
SEEDS=[20260709,20260710,20260711]
MODELS={"openai":"gpt-5.4-nano","google":"gemini-3.5-flash"}
PRICES={"gpt-5.4-nano":(0.20,1.25),"gemini-3.5-flash":(1.50,9.00)}
MAX_OUTPUT_TOKENS=1024   # reasoning models (gpt-5.x-nano) burn tokens on hidden reasoning;
                         # 256 left empty completions. 1024 gives headroom for a real answer.
MAX_SPEND_USD=20.0

# ---- keys (env wins; sibling keys.env.txt convenience) ----
def load_keys():
    f=HERE.parents[1]/"API Keys"/"keys.env.txt"
    if not f.exists(): return
    for line in f.read_text().splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k,v=line.split("=",1); k,v=k.strip(),v.strip().strip('"').strip("'")
        if v and not os.environ.get(k): os.environ[k]=v
load_keys()
def key_for(prov):
    for k in {"openai":["OPENAI_API_KEY"],"google":["GOOGLE_API_KEY","GEMINI_API_KEY"]}[prov]:
        if os.environ.get(k): return os.environ[k]
    raise RuntimeError(f"no API key for {prov} (set in ../../API Keys/keys.env.txt)")

# ---- API calls (reused from Phase B collect.py) ----
def _http_json(url,payload,headers,timeout=90):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers=headers,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}") from None

def call_openai(model,prompt,seed):
    hdr={"Content-Type":"application/json","Authorization":f"Bearer {key_for('openai')}"}
    base={"model":model,"messages":[{"role":"user","content":prompt}]}
    for extra in ({"max_completion_tokens":MAX_OUTPUT_TOKENS,"seed":seed,"reasoning_effort":"low"},
                  {"max_completion_tokens":MAX_OUTPUT_TOKENS,"seed":seed},
                  {"max_completion_tokens":MAX_OUTPUT_TOKENS}):
        try:
            j=_http_json("https://api.openai.com/v1/chat/completions",dict(base,**extra),hdr)
            txt=j["choices"][0]["message"]["content"] or ""; u=j.get("usage",{})
            return txt,u.get("prompt_tokens",0),u.get("completion_tokens",0)
        except RuntimeError as e:
            if "HTTP 400" in str(e): continue
            raise
    return "",0,0

def call_google(model,prompt,seed):
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key_for('google')}"
    gen={"maxOutputTokens":MAX_OUTPUT_TOKENS,"seed":seed,"thinkingConfig":{"thinkingBudget":0}}
    body={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":gen}
    try: j=_http_json(url,body,{"Content-Type":"application/json"})
    except RuntimeError as e:
        if "HTTP 400" in str(e):
            gen.pop("thinkingConfig",None); j=_http_json(url,body,{"Content-Type":"application/json"})
        else: raise
    cand=(j.get("candidates") or [{}])[0]
    txt="".join(p.get("text","") for p in cand.get("content",{}).get("parts",[]))
    um=j.get("usageMetadata",{})
    return txt,um.get("promptTokenCount",0),um.get("candidatesTokenCount",0)

def mock_call(model,prompt,seed):
    h=int(hashlib.sha256(f"{model}|{prompt}|{seed}".encode()).hexdigest(),16)
    return ("UNKNOWN" if h%4 else "My best guess: UNKNOWN"),len(prompt)//4,3
ROUTER={"openai":call_openai,"google":call_google}

# ---- fingerprint prompt (anonymized facts ONLY) ----
def fp_prompt(item):
    return ("Below are selected financial figures from the most recent fiscal year of ONE real, "
            "publicly-listed US company (all identifying details removed). Using only these figures, "
            "identify the SPECIFIC company you believe they belong to.\n\n"
            f"{item['facts_text']}\n\n"
            "Answer with your single best guess as a company name or stock ticker. If you genuinely "
            "cannot identify a specific company, answer exactly: UNKNOWN. "
            "Format: 'GUESS: <name or ticker>' on one line.")

def price(model,i,o):
    pin,pout=PRICES[model]; return i/1e6*pin+o/1e6*pout

def main():
    items=json.load(open(HERE/"battery_real45.json"))["items"]
    spend=0.0; done=0; empties=0; calls=[]
    TOTAL=len(items)*len(MODELS)*len(SEEDS)
    print(f"PHASE 3 fingerprint pilot — {TOTAL} calls ({len(items)} items x {len(MODELS)} models x {len(SEEDS)} seeds)  {'[MOCK]' if MOCK else ''}")
    for it in items:
        for prov,model in MODELS.items():
            for seed in SEEDS:
                fp=RAW/f"{it['item_id']}_{prov}_s{seed}.json"
                if fp.exists():
                    try:
                        d=json.loads(fp.read_text())
                        if d.get("ok"): calls.append(d); done+=1; continue
                    except Exception: pass
                if spend>MAX_SPEND_USD:
                    print(f"!! spend ${spend:.2f} exceeds cap ${MAX_SPEND_USD}; STOP"); break
                prompt=fp_prompt(it)
                try:
                    txt,i,o=(mock_call if MOCK else ROUTER[prov])(model,prompt,seed)
                    c=price(model,i,o); spend+=c
                    rec={"item_id":it["item_id"],"provider":prov,"model":model,"seed":seed,
                         "ok":bool(txt.strip()),"raw_response":txt,"in_tok":i,"out_tok":o,"usd":round(c,6),
                         "utc":datetime.now(timezone.utc).isoformat()}
                    fp.write_text(json.dumps(rec,indent=1)); calls.append(rec); done+=1
                    if not txt.strip(): empties+=1
                    g=(re.search(r"GUESS:\s*(.+)",txt) or [None,txt.strip()[:40]])[1] or "(empty)"
                    pct=100*done/TOTAL
                    print(f"  [{done:3d}/{TOTAL} {pct:5.1f}%] {it['item_id']} {prov:6} s{seed}: "
                          f"{str(g)[:40]:40} (${spend:.3f}{' EMPTY' if not txt.strip() else ''})")
                except Exception as e:
                    print(f"  {it['item_id']} {prov:6} s{seed}: ERROR {e}")
                    time.sleep(2)
    score(calls,spend)

def norm(s): return re.sub(r"[^a-z0-9 ]"," ",s.lower())
STOP={"corp","corporation","inc","co","company","the","holdings","group","technologies",
      "technology","ltd","plc","llc","international","industries","and"}
def score(calls,spend):
    keyrows=json.load(open(HERE/"sealed_scoring_key.json"))["key"]
    K={k["item_id"]:k for k in keyrows}
    # data-quality: empty/missing completions per provider
    from collections import Counter
    tot=Counter(); emp=Counter()
    for c in calls:
        tot[c["provider"]]+=1
        if not (c.get("ok") and (c.get("raw_response") or "").strip()): emp[c["provider"]]+=1
    dq={p:{"calls":tot[p],"empty":emp[p],"empty_pct":round(100*emp[p]/max(1,tot[p]),1)} for p in tot}
    per_run={}; ident_runs={}
    for c in calls:
        if not c.get("ok"): continue
        k=K[c["item_id"]]; resp=norm(c["raw_response"])
        tk=k["ticker"].lower()
        name_tokens=[t for t in norm(k["entity_name"] or "").split() if t not in STOP and len(t)>2]
        hit_ticker=bool(re.search(rf"(?<![a-z0-9]){re.escape(tk)}(?![a-z0-9])",resp)) and k["ticker"].isalpha() and len(tk)>=2
        hit_name=bool(name_tokens) and all(t in resp for t in name_tokens[:2]) if len(name_tokens)>=2 else (bool(name_tokens) and name_tokens[0] in resp)
        hit=hit_ticker or hit_name
        per_run.setdefault(c["item_id"],[]).append(hit)
        ident_runs.setdefault(c["item_id"],0)
        if hit: ident_runs[c["item_id"]]+=1
    n_items=len(K)
    ever=[iid for iid,n in ident_runs.items() if n>=1]           # primary (lenient): any run
    twice=[iid for iid,n in ident_runs.items() if n>=2]          # robust: >=2 runs
    total_runs=sum(len(v) for v in per_run.values())
    hit_runs=sum(sum(v) for v in per_run.values())
    share_ever=len(ever)/n_items; share_twice=len(twice)/n_items
    gate=("GO" if share_ever<0.05 else "RE-TEST" if share_ever<=0.15 else "NO-GO")
    out={"utc":datetime.now(timezone.utc).isoformat(),"n_items":n_items,
         "data_quality_empty_by_provider":dq,
         "calls_scored":total_runs,"per_run_identification_rate":round(hit_runs/max(1,total_runs),4),
         "per_item_ever_identified":{"n":len(ever),"share":round(share_ever,4),"items":sorted(ever)},
         "per_item_twice_identified":{"n":len(twice),"share":round(share_twice,4),"items":sorted(twice)},
         "gate_metric":"per_item_ever_identified.share (pre-registered)",
         "gate_thresholds":"<5% GO | 5-15% RE-TEST | >15% NO-GO",
         "GATE":gate,"spend_usd":round(spend,4)}
    out["run_id"]=RUN_ID; out["run_dir"]=str(RUN_DIR.relative_to(HERE))
    RESULT_PATH.write_text(json.dumps(out,indent=1))
    print("\n=== PHASE 3 RESULT ===")
    print(f"run: {RUN_DIR.relative_to(HERE)}")
    print(f"per-run id rate     : {out['per_run_identification_rate']*100:.1f}%  ({hit_runs}/{total_runs})")
    print(f"per-item ever-id    : {len(ever)}/{n_items} = {share_ever*100:.1f}%   items={sorted(ever)}")
    print(f"per-item >=2-run id : {len(twice)}/{n_items} = {share_twice*100:.1f}%")
    print(f"GATE ({'<5% GO / 5-15% RE-TEST / >15% NO-GO'}): {gate}")
    print(f"spend: ${spend:.4f}")

if __name__=="__main__": main()
