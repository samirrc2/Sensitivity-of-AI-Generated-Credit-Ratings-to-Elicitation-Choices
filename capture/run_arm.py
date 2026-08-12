#!/usr/bin/env python3
"""Appendix D — Real-firm arm · PHASE 4 main run (H1). LOCAL execution (sandbox can't reach APIs).

Runs the frozen 12-spec x 3-seed grid over the 31 ANONYMIZED, PERTURBED B2B firms (battery_real45.json),
asking each pinned model for a 21-grade letter rating (same credit_health task as Phase B), then maps
the letter -> band (SAFE/WATCH/DISTRESS) for the flip-share analysis. Stores one immutable JSON per call
(resume-safe, timestamped run folder, never clobbers old runs). Hard cost stop $20 (expected ~$1.59).

RUN:   python3 run_arm.py            # keys auto-load from ../../API Keys/keys.env.txt
       PILOT_MOCK=1 python3 run_arm.py    # offline dry-run, no keys/spend
       FP_NEW_RUN=1 python3 run_arm.py    # force a brand-new run folder
"""
from __future__ import annotations
import os, json, time, re, hashlib, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
FROZEN=HERE.parents[0]/"phaseB"/"00_frozen_inputs"   # reuse frozen paraphrase templates
MOCK=os.environ.get("PILOT_MOCK")=="1"
SEEDS=[20260709,20260710,20260711]
MAX_OUTPUT_TOKENS=1024
MAX_SPEND_USD=20.0
PRICES={"gpt-5.4-nano":(0.20,1.25),"gemini-3.5-flash":(1.50,9.00)}

# reusable for the battery comparator: ARM_BATTERY picks the item file, ARM_RUNS_DIR the output root
BATTERY_FILE=Path(os.environ.get("ARM_BATTERY", str(HERE/"battery_real45.json")))
RUNS=HERE/os.environ.get("ARM_RUNS_DIR","arm_runs"); RUNS.mkdir(exist_ok=True)
_ACTIVE=RUNS/".active_run"
if MOCK: RUN_ID="mock"
elif os.environ.get("FP_RUN_ID"): RUN_ID=os.environ["FP_RUN_ID"]
elif _ACTIVE.exists() and os.environ.get("FP_NEW_RUN")!="1": RUN_ID=_ACTIVE.read_text().strip()
else: RUN_ID=datetime.now().strftime("%Y%m%d_%H%M%S")
RUN_DIR=RUNS/("run_mock" if MOCK else f"run_{RUN_ID}"); RAW=RUN_DIR/"raw"; RAW.mkdir(parents=True,exist_ok=True)
if not MOCK: _ACTIVE.write_text(RUN_ID)

def load_keys():
    f=HERE.parents[1]/"API Keys"/"keys.env.txt"
    if not f.exists(): return
    for line in f.read_text().splitlines():
        line=line.strip()
        if line and not line.startswith("#") and "=" in line:
            k,v=line.split("=",1); k,v=k.strip(),v.strip().strip('"').strip("'")
            if v and not os.environ.get(k): os.environ[k]=v
load_keys()
def key_for(p):
    for k in {"openai":["OPENAI_API_KEY"],"google":["GOOGLE_API_KEY","GEMINI_API_KEY"]}[p]:
        if os.environ.get(k): return os.environ[k]
    raise RuntimeError(f"no API key for {p}")

TPL=json.load(open(FROZEN/"paraphrase_templates.json"))
_b=json.load(open(BATTERY_FILE)); ITEMS=_b["items"] if isinstance(_b,dict) else _b   # real arm dict / battery_90 list
ITEMS=[it for it in ITEMS if it.get("benchmark_label") in ("SAFE","WATCH","DISTRESS")]  # credit items only (drop directional)
SPECS=json.load(open(HERE/"spec_grid_12.json"))["specs"]
FAM="credit_health"     # 21-grade letter task, identical to Phase B

ORDER=["AAA","AA+","AA","AA-","A+","A","A-","BBB+","BBB","BBB-","BB+","BB","BB-","B+","B","B-","CCC+","CCC","CCC-","CC","C"]
def rating_to_band(sp):
    if sp not in ORDER: return None
    i=ORDER.index(sp); return "SAFE" if i<=ORDER.index("BBB-") else "WATCH" if i<=ORDER.index("B-") else "DISTRESS"

def render_facts(item,lvl_name):
    lvl=TPL["presentation_levels"][lvl_name]
    kv=list(reversed(item["facts_kv"])) if lvl["order"]=="reversed" else item["facts_kv"][:]
    if lvl["layout"]=="table" and kv:
        w=max(len(k) for k,_ in kv); return "\n".join(f"| {k.ljust(w)} | {v} |" for k,v in kv)
    return item["facts_text"]
def build_prompt(item,spec):
    fam=TPL["families"][FAM]
    return TPL["paraphrases"][spec["A4_paraphrase"]].format(
        role=fam["role"],question=fam["question"],labels=", ".join(fam["labels"]),
        asof="the most recent fiscal year",
        facts_block=render_facts(item,"L1" if spec["A7_presentation"].startswith("L1") else "L0"),
        fewshot_block="",format_block=TPL["format_blocks"][spec["A5_format"]])

def _http(url,payload,hdr,timeout=90):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers=hdr,method="POST")
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:200]}") from None
def call_openai(model,prompt,seed):
    hdr={"Content-Type":"application/json","Authorization":f"Bearer {key_for('openai')}"}
    base={"model":model,"messages":[{"role":"user","content":prompt}]}
    for extra in ({"max_completion_tokens":MAX_OUTPUT_TOKENS,"seed":seed,"reasoning_effort":"low"},
                  {"max_completion_tokens":MAX_OUTPUT_TOKENS,"seed":seed},{"max_completion_tokens":MAX_OUTPUT_TOKENS}):
        try:
            j=_http("https://api.openai.com/v1/chat/completions",dict(base,**extra),hdr)
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
    try: j=_http(url,body,{"Content-Type":"application/json"})
    except RuntimeError as e:
        if "HTTP 400" in str(e): gen.pop("thinkingConfig",None); j=_http(url,body,{"Content-Type":"application/json"})
        else: raise
    cand=(j.get("candidates") or [{}])[0]
    txt="".join(p.get("text","") for p in cand.get("content",{}).get("parts",[]))
    um=j.get("usageMetadata",{}); return txt,um.get("promptTokenCount",0),um.get("candidatesTokenCount",0)
def mock_call(model,prompt,seed):
    h=int(hashlib.sha256(f"{model}|{prompt}|{seed}".encode()).hexdigest(),16)
    return json.dumps({"rating":ORDER[h%len(ORDER)]}),len(prompt)//4,8
ROUTER={"openai":call_openai,"google":call_google}

GRADE=re.compile(r"(?<![A-Za-z0-9])(AAA|AA[+-]?|A[+-]?|BBB[+-]?|BB[+-]?|B[+-]?|CCC[+-]?|CC|C)(?![A-Za-z0-9])")
def parse_letter(txt):
    m=re.search(r'"rating"\s*:\s*"([^"]+)"',txt) or re.search(r'\brating\b[^A-Za-z0-9]{0,6}([A-C]{1,3}[+-]?)',txt,re.I)
    if m:
        g=m.group(1).upper().replace(" ","")
        if g in ORDER: return g
    cands=GRADE.findall(txt)
    return cands[-1] if cands else None
def price(model,i,o): pin,pout=PRICES[model]; return i/1e6*pin+o/1e6*pout

def main():
    TOTAL=len(ITEMS)*len(SPECS)*len(SEEDS); spend=0.0; done=0; empt=0; rows=[]
    print(f"PHASE 4 arm main run — {TOTAL} calls ({len(ITEMS)} items x {len(SPECS)} specs x {len(SEEDS)} seeds)  {'[MOCK]' if MOCK else ''}")
    for it in ITEMS:
        for sp in SPECS:
            prov=sp["A1_provider"]; model=sp["model"]
            for seed in SEEDS:
                fp=RAW/f"{sp['spec_id']}_{it['item_id']}_s{seed}.json"
                if fp.exists():
                    try:
                        d=json.loads(fp.read_text())
                        if d.get("ok"): rows.append(d); done+=1; continue
                    except Exception: pass
                if spend>MAX_SPEND_USD: print(f"!! cap ${MAX_SPEND_USD} hit; STOP"); break
                prompt=build_prompt(it,sp)
                try:
                    txt,i,o=(mock_call if MOCK else ROUTER[prov])(model,prompt,seed)
                    c=price(model,i,o); spend+=c
                    letter=parse_letter(txt); band=rating_to_band(letter) if letter else None
                    rec={"spec_id":sp["spec_id"],"item_id":it["item_id"],"benchmark_label":it.get("benchmark_label"),"provider":prov,"model":model,"seed":seed,
                         "presentation":sp["A7_presentation"],"paraphrase":sp["A4_paraphrase"],"format":sp["A5_format"],
                         "ok":bool(txt.strip()),"raw_response":txt,"parsed_letter":letter,"parsed_band":band,
                         "in_tok":i,"out_tok":o,"usd":round(c,6),"utc":datetime.now(timezone.utc).isoformat()}
                    fp.write_text(json.dumps(rec,indent=1)); rows.append(rec); done+=1
                    if not txt.strip(): empt+=1
                    pct=100*done/TOTAL
                    print(f"  [{done:4d}/{TOTAL} {pct:5.1f}%] {sp['spec_id']} {it['item_id']} {prov:6} s{seed}: "
                          f"{str(letter or '(empty)'):5}->{str(band or '?'):8} (${spend:.3f})")
                except Exception as e:
                    print(f"  {sp['spec_id']} {it['item_id']} {prov} s{seed}: ERROR {e}"); time.sleep(2)
    # write panel
    from collections import Counter
    ok=[r for r in rows if r.get("parsed_band")]
    panel={"utc":datetime.now(timezone.utc).isoformat(),"run_id":RUN_ID,"n_calls":len(rows),
           "n_parsed":len(ok),"empty":sum(1 for r in rows if not r.get("ok")),
           "band_dist":dict(Counter(r["parsed_band"] for r in ok)),
           "by_provider_empty":dict(Counter(r["provider"] for r in rows if not r.get("ok"))),
           "rows":rows}
    (RUN_DIR/"arm_panel.json").write_text(json.dumps(panel,indent=1))
    print(f"\n=== PHASE 4 DONE ===\nrun: {RUN_DIR.relative_to(HERE)}")
    print(f"calls {len(rows)}/{TOTAL} | parsed {len(ok)} | empty {panel['empty']} {panel['by_provider_empty']}")
    print(f"band distribution: {panel['band_dist']}")
    print(f"spend ${spend:.4f}  -> arm_panel.json written; run analyze_arm.py (Phase 5) for H1 flip-share")

if __name__=="__main__": main()
