#!/usr/bin/env python3
# =============================================================================
# ONE-RUN RULE (verbatim):
#   "After this run terminates and MANIFEST_RAW.sha256 is written, no cell is ever
#    re-collected for any reason. Dead cells, refusals, and gaps are findings."
# =============================================================================
"""P3 Phase B collection — SINGLE RUN, submission-ready. LOCAL execution only
(the analysis sandbox cannot reach provider APIs).

Grid: 48 specs x 90 items x 3 seeds = 12,960 calls. Reads ONLY ../00_frozen_inputs/
(battery_90.json, grid_definition.json, paraphrase_templates.json). One immutable
JSON per call to raw/. Resume-safe WITHIN this run (crash-restart continues from the
files already written; never re-calls a completed cell). Retry max 2 with exponential
backoff, then the cell is recorded MISSING permanently. Empty completions after retries
are MISSING. Hard abort at $300 cumulative. Live collection_log.csv + per-provider spend.
If total missingness > 10% of cells, STOP after hashing and await instruction (no patching).

Run:
  export OPENAI_API_KEY=...   GOOGLE_API_KEY=...   XAI_API_KEY=...
  python3 collect.py
  # offline pipeline check (no keys, no spend): PILOT_MOCK=1 python3 collect.py
"""
from __future__ import annotations
import os, sys, json, csv, time, hashlib, threading, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent                 # 01_collection/
FROZEN = HERE.parent / "00_frozen_inputs"
MOCK = os.environ.get("PILOT_MOCK") == "1"

# ---- run isolation: every run has its own timestamped folder --------------------
# RUN_ID resolution: explicit F3_RUN_ID wins; else resume the .active_run if present
# (unless F3_NEW_RUN=1); else mint a new timestamp. Each run is fully self-contained.
_ACTIVE = HERE / ".active_run"
if MOCK:
    RUN_ID = "mock"
elif os.environ.get("F3_RUN_ID"):
    RUN_ID = os.environ["F3_RUN_ID"]
elif _ACTIVE.exists() and os.environ.get("F3_NEW_RUN") != "1":
    RUN_ID = _ACTIVE.read_text().strip()
else:
    RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
if not MOCK:
    _ACTIVE.write_text(RUN_ID)
RUN_DIR = HERE / ("raw_mock" if MOCK else f"run_{RUN_ID}")
RAW = RUN_DIR / "raw"; RAW.mkdir(parents=True, exist_ok=True)
LOG = RUN_DIR / "collection_log.csv"
MANIFEST_RAW_PATH = RUN_DIR / "MANIFEST_RAW.sha256"
SPEND_PATH = RUN_DIR / "spend_report.md"

# ---- FROZEN run parameters -----------------------------------------------------
SEEDS = [11, 22, 33]                    # amendment: 2 -> 3 seeds (noise floor headline)
MAX_SPEND_USD = 300.0                   # hard stop
MAX_RETRIES = 2
MAX_OUTPUT_TOKENS = 1024
OPENAI_REASONING_EFFORT = "low"
GEMINI_DISABLE_THINKING = True
MISSINGNESS_STOP_FRAC = 0.10
CONCURRENCY = int(os.environ.get("F3_CONCURRENCY", "24"))   # parallel worker threads
RPM_LIMITS = {"openai": 500, "google": 300, "xai": 180}     # per-provider requests/min caps
# Execution order does NOT affect the frozen result: each cell writes its own immutable
# file; analysis (B2+) is an order-independent function of raw/. Concurrency is purely a
# wall-clock optimisation, matching the Paper 1/2 orchestrators.


class RateLimiter:
    """Global min-interval limiter shared across worker threads for one provider."""
    def __init__(self, rpm):
        self.min_interval = (60.0 / rpm) if rpm and rpm > 0 else 0.0
        self.lock = threading.Lock(); self.next_time = 0.0

    def acquire(self):
        if self.min_interval <= 0:
            return
        with self.lock:
            now = time.monotonic(); t = max(now, self.next_time)
            self.next_time = t + self.min_interval; wait = t - now
        if wait > 0:
            time.sleep(wait)

# Pinned model snapshots (A1 x A2).  *** VERIFY exact strings before the single run ***
# NOTE: xai/prior grok-4.1-fast was 100% EMPTY in Phase A (deviations_addendum, KNOWN RISK).
# Either accept it as a dead cell (>10% missingness stop will fire) or edit this ONE line
# to a verified working Grok snapshot before running. Record the substitution in the addendum.
MODELS = {
    ("openai", "current"): "gpt-5.4-nano",             # VERIFY
    ("openai", "prior"):   "gpt-5-nano-2025-08-07",    # VERIFY
    ("google", "current"): "gemini-3.5-flash",         # VERIFY
    ("google", "prior"):   "gemini-2.5-flash",         # VERIFY
    ("xai",    "current"): "grok-4.3",                 # VERIFY
    ("xai",    "prior"):   "grok-4.1-fast",            # VERIFY / KNOWN-DEAD in Phase A
}
PRICES = {  # per-1M (input, output) USD -- VERIFY
    "gpt-5.4-nano": (0.20, 1.25), "gpt-5-nano-2025-08-07": (0.20, 1.25),
    "gemini-3.5-flash": (1.50, 9.00), "gemini-2.5-flash": (0.30, 2.50),
    "grok-4.3": (1.25, 2.50), "grok-4.1-fast": (0.50, 1.50),
}

# ---- keys (env only per spec; sibling keys.env.txt loaded as a convenience, env wins) ----
_KEYMAP = {"openai": ["OPENAI_API_KEY"], "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
           "xai": ["XAI_API_KEY"]}


def load_keys_env():
    f = HERE.parents[2] / "API Keys" / "keys.env.txt"     # NIW/API Keys/keys.env.txt
    if not f.exists():
        return
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1); k, v = k.strip(), v.strip().strip('"').strip("'")
        if v and not os.environ.get(k):
            os.environ[k] = v


load_keys_env()


def key_for(prov):
    for name in _KEYMAP[prov]:
        if os.environ.get(name):
            return os.environ[name]
    return None


# ---- frozen inputs -------------------------------------------------------------
ITEMS = json.load(open(FROZEN / "battery_90.json"))
TPL = json.load(open(FROZEN / "paraphrase_templates.json"))
SPECS = json.load(open(FROZEN / "grid_definition.json"))["specs"]
AXES = ["A2_version", "A3_temperature", "A4_paraphrase", "A5_format", "A6_fewshot", "A7_presentation"]


# ---- prompt construction (A4-A7) ----------------------------------------------
def render_facts(item, presentation_level):
    lvl = TPL["presentation_levels"][presentation_level]
    kv = list(reversed(item["facts_kv"])) if lvl["order"] == "reversed" else item["facts_kv"][:]
    if lvl["layout"] == "table" and kv:
        w = max(len(k) for k, _ in kv)
        return "\n".join(f"| {k.ljust(w)} | {v} |" for k, v in kv)
    return item["facts_text"]


def render_fewshot(family, n):
    if n == 0:
        return ""
    ex = TPL["fewshot_exemplars"][family]
    return "Here are two worked examples:\n" + "\n".join(
        f"- Information: {e['facts_text']}\n  Answer: {e['label']}" for e in ex[:2]) + "\n\n"


def build_prompt(item, spec):
    fam = TPL["families"][item["family"]]
    return TPL["paraphrases"][spec["A4_paraphrase"]].format(
        role=fam["role"], question=fam["question"], labels=", ".join(fam["labels"]),
        asof=item.get("asof") or item["cell_date"],
        facts_block=render_facts(item, "L1" if spec["A7_presentation"].startswith("L1") else "L0"),
        fewshot_block=render_fewshot(item["family"], int(spec["A6_fewshot"])),
        format_block=TPL["format_blocks"][spec["A5_format"]])


# ---- provider routers ----------------------------------------------------------
def _http_json(url, payload, headers, timeout=90):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:400]}") from None


def _oai_compatible(url, key, model, prompt, temperature, seed):
    hdr = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    base = {"model": model, "messages": [{"role": "user", "content": prompt}]}
    eff = {"reasoning_effort": OPENAI_REASONING_EFFORT}
    sigs = [("mct+temp+seed+eff", {"max_completion_tokens": MAX_OUTPUT_TOKENS, "temperature": temperature, "seed": seed, **eff}),
            ("mct+seed+eff", {"max_completion_tokens": MAX_OUTPUT_TOKENS, "seed": seed, **eff}),
            ("mct+eff", {"max_completion_tokens": MAX_OUTPUT_TOKENS, **eff}),
            ("mct+temp+seed", {"max_completion_tokens": MAX_OUTPUT_TOKENS, "temperature": temperature, "seed": seed}),
            ("mct+seed", {"max_completion_tokens": MAX_OUTPUT_TOKENS, "seed": seed}),
            ("mct", {"max_completion_tokens": MAX_OUTPUT_TOKENS})]
    last = None
    for name, extra in sigs:
        try:
            j = _http_json(url, dict(base, **extra), hdr)
            txt = j["choices"][0]["message"]["content"] or ""; u = j.get("usage", {})
            return txt, u.get("prompt_tokens", 0), u.get("completion_tokens", 0), {
                "signature": name, "temperature_applied": "temperature" in extra,
                "reasoning_effort": OPENAI_REASONING_EFFORT if "reasoning_effort" in extra else None,
                "request_params": {k: extra[k] for k in extra}}
        except RuntimeError as e:
            last = e
            if "HTTP 400" in str(e):
                continue
            raise
    raise last


def call_openai(model, prompt, temperature, seed):
    return _oai_compatible("https://api.openai.com/v1/chat/completions", key_for("openai"), model, prompt, temperature, seed)


def call_xai(model, prompt, temperature, seed):
    return _oai_compatible("https://api.x.ai/v1/chat/completions", key_for("xai"), model, prompt, temperature, seed)


def call_google(model, prompt, temperature, seed):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key_for('google')}"
    gen = {"temperature": temperature, "maxOutputTokens": MAX_OUTPUT_TOKENS, "seed": seed}
    nothink = False
    if GEMINI_DISABLE_THINKING:
        gen["thinkingConfig"] = {"thinkingBudget": 0}; nothink = True
    body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": gen}
    try:
        j = _http_json(url, body, {"Content-Type": "application/json"})
    except RuntimeError as e:
        if "HTTP 400" in str(e) and nothink:
            gen.pop("thinkingConfig", None); nothink = False
            j = _http_json(url, body, {"Content-Type": "application/json"})
        else:
            raise
    cand = (j.get("candidates") or [{}])[0]
    txt = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
    um = j.get("usageMetadata", {})
    return txt, um.get("promptTokenCount", 0), um.get("candidatesTokenCount", 0), {
        "temperature_applied": True, "gemini_no_thinking": nothink, "request_params": gen}


ROUTER = {"openai": call_openai, "google": call_google, "xai": call_xai}


def mock_call(model, prompt, temperature, seed):
    h = int(hashlib.sha256(f"{model}|{prompt}|{seed}".encode()).hexdigest(), 16)
    labs = ["SAFE", "WATCH", "DISTRESS"] if ("credit" in prompt.lower() or "SAFE" in prompt) else ["BUY", "HOLD", "SELL"]
    txt = json.dumps({"decision": labs[h % 3], "confidence": (h % 5) + 1, "rationale": "mock"})
    return txt, max(1, len(prompt) // 4), max(1, len(txt) // 4), {"temperature_applied": True, "request_params": {}}


def price(model, itok, otok):
    pin, pout = PRICES.get(model, (0.0, 0.0)); return itok / 1e6 * pin + otok / 1e6 * pout


def raw_path(spec_id, item_id, seed):
    return RAW / f"{spec_id}_{item_id}_s{seed}.json"


def already_done(fp):
    if not fp.exists():
        return False
    try:
        d = json.loads(fp.read_text())
        return bool(d.get("ok")) and bool((d.get("raw_response") or "").strip())
    except Exception:
        return False


def project_cost(avg_in=300, avg_out=250):
    tot = 0.0
    for spec in SPECS:
        m = MODELS[(spec["A1_provider"], spec["A2_version"])]
        tot += len(ITEMS) * len(SEEDS) * price(m, avg_in, avg_out)
    return tot


def main():
    ncalls = len(SPECS) * len(ITEMS) * len(SEEDS)
    proj = project_cost()
    print(f"[B1] RUN_ID = {RUN_ID}   ->  run folder: 01_collection/{RUN_DIR.name}/")
    print(f"[B1] (resume this run: F3_RUN_ID={RUN_ID} python3 collect.py | fresh run: F3_NEW_RUN=1 python3 collect.py)")
    print(f"[B1] grid: {len(SPECS)} specs x {len(ITEMS)} items x {len(SEEDS)} seeds = {ncalls} calls | "
          f"mode={'MOCK' if MOCK else 'REAL'}")
    print(f"[B1] projected cost ~${proj:.2f} (hard stop ${MAX_SPEND_USD:.0f})")
    provs = sorted(set(s["A1_provider"] for s in SPECS))
    have = {p for p in provs if MOCK or key_for(p)}
    if set(provs) - have and not MOCK:
        print(f"[B1] MISSING KEYS for {sorted(set(provs)-have)} -> those cells recorded MISSING.")

    new_log = not LOG.exists()
    logf = open(LOG, "a", newline=""); logw = csv.writer(logf)
    if new_log:
        logw.writerow(["ts", "spec_id", "item_id", "seed", "provider", "version", "model",
                       "ok", "empty", "attempts", "cost_usd", "error"])
    limiters = {p: RateLimiter(0 if MOCK else RPM_LIMITS.get(p, 0)) for p in provs}
    # build the task list (skip already-completed cells -> resume-safe within the run)
    item_by = {it["item_id"]: it for it in ITEMS}
    tasks = [(spec, it, seed) for spec in SPECS for it in ITEMS for seed in SEEDS
             if not already_done(raw_path(spec["spec_id"], it["item_id"], seed))]
    print(f"[B1] concurrency: {CONCURRENCY} workers | rpm limits {RPM_LIMITS} | "
          f"{len(tasks)} cells to do (rest already on disk).")

    st = {"spend": {p: 0.0 for p in provs}, "done": 0, "missing": 0, "stop": False}
    lock = threading.Lock()

    def worker(task):
        spec, it, seed = task
        prov, ver = spec["A1_provider"], spec["A2_version"]
        model = MODELS[(prov, ver)]; temp = float(spec["A3_temperature"])
        fp = raw_path(spec["spec_id"], it["item_id"], seed)
        if prov not in have:
            fp.write_text(json.dumps({"spec_id": spec["spec_id"], "item_id": it["item_id"], "seed": seed,
                          "provider": prov, "version": ver, "model": model, "ok": False, "empty": False,
                          "raw_response": "", "error": "NO_API_KEY", "timestamp_utc": _ts()}, indent=1))
            _record(st, lock, logw, logf, spec, it, seed, prov, ver, model, False, False, 0, 0.0, "NO_API_KEY", ncalls)
            return
        wc = price(model, 300, MAX_OUTPUT_TOKENS)
        with lock:
            if st["stop"] or sum(st["spend"].values()) + wc > MAX_SPEND_USD:
                st["stop"] = True; return
        prompt = build_prompt(it, spec)
        res = None; err = None; meta = {}; attempts = 0
        for attempt in range(1, MAX_RETRIES + 2):
            attempts = attempt
            try:
                if not MOCK:
                    limiters[prov].acquire()
                fn = mock_call if MOCK else ROUTER[prov]
                txt, itok, otok, meta = fn(model, prompt, temp, seed)
                res = (txt, itok, otok); break
            except Exception as e:
                err = f"{type(e).__name__}: {str(e)[:200]}"
                if attempt <= MAX_RETRIES:
                    time.sleep(1.5 * (2 ** (attempt - 1)))
        empty = bool(res) and not (res[0] or "").strip()
        ok = bool(res) and not empty
        cost = price(model, res[1], res[2]) if res else 0.0
        applied = meta.get("temperature_applied", True)
        row = {"spec_id": spec["spec_id"], "item_id": it["item_id"], "seed": seed,
               "family": it["family"], "provider": prov, "version": ver, "model": model,
               "benchmark_label": it["benchmark_label"],
               "axes": {a: spec[a] for a in AXES}, "A1_provider": prov,
               "requested_temperature": temp, "temperature_applied": applied,
               "effective_temperature": (temp if applied else None),
               "call_meta": meta, "prompt": prompt,
               "raw_response": (res[0] if res else ""), "empty": empty, "ok": ok,
               "input_tokens": (res[1] if res else 0), "output_tokens": (res[2] if res else 0),
               "cost_usd": round(cost, 6), "attempts": attempts,
               "error": (None if ok else (err or ("EMPTY" if empty else "MISSING"))),
               "timestamp_utc": _ts(), "mode": "MOCK" if MOCK else "REAL"}
        fp.write_text(json.dumps(row, indent=1))
        _record(st, lock, logw, logf, spec, it, seed, prov, ver, model, ok, empty, attempts, cost, row["error"], ncalls)

    with ThreadPoolExecutor(max_workers=CONCURRENCY) as ex:
        list(ex.map(worker, tasks))
    logf.close()
    if st["stop"]:
        print(f"[B1] HARD STOP: ${MAX_SPEND_USD} cap guard tripped.")
    _finalize(st["spend"], st["done"], st["missing"], ncalls, st["stop"])


def _record(st, lock, logw, logf, spec, it, seed, prov, ver, model, ok, empty, attempts, cost, error, ncalls):
    with lock:
        if ok:
            st["spend"][prov] += cost; st["done"] += 1
        else:
            st["missing"] += 1
        logw.writerow([_ts(), spec["spec_id"], it["item_id"], seed, prov, ver, model, ok, empty, attempts, round(cost, 6), error]); logf.flush()
        n = st["done"] + st["missing"]
        if n % 200 == 0:
            print(f"  ...{st['done']} ok, {st['missing']} missing; spend ${sum(st['spend'].values()):.2f}")


def _ts():
    return datetime.now(timezone.utc).isoformat()


def _write_missing(fp, spec, it, seed, model, reason):
    fp.write_text(json.dumps({"spec_id": spec["spec_id"], "item_id": it["item_id"], "seed": seed,
                              "provider": spec["A1_provider"], "version": spec["A2_version"], "model": model,
                              "ok": False, "empty": False, "raw_response": "", "error": reason,
                              "timestamp_utc": _ts()}, indent=1))


def _finalize(spend, done, missing, ncalls, stop):
    # 1) Persist the hash FIRST over whatever raw/ files exist -> nothing is ever lost,
    #    even if this run was a crash-restart. 2) Count ok/missing AUTHORITATIVELY from
    #    the raw files on disk (not the per-invocation counters), so the missingness
    #    figure is correct regardless of restarts. 3) The >10% stop is a POST-HASH
    #    report only -- it never aborts the loop (only the $300 hard-stop does).
    h = hashlib.sha256(); files = sorted(RAW.glob("*.json"))
    disk_ok = disk_missing = 0
    for p in files:
        h.update(p.read_bytes())
        try:
            d = json.loads(p.read_text())
            if d.get("ok") and (d.get("raw_response") or "").strip():
                disk_ok += 1
            else:
                disk_missing += 1
        except Exception:
            disk_missing += 1
    digest = h.hexdigest()
    MANIFEST_RAW_PATH.write_text(digest + "\n")
    attempted = disk_ok + disk_missing
    miss_frac = disk_missing / ncalls if ncalls else 0
    sr = ["# Phase B spend report", "", f"- run_id: {RUN_ID}", f"- mode: {'MOCK' if MOCK else 'REAL'}",
          f"- cells on disk: {attempted} / {ncalls} grid",
          f"- ok (non-empty): {disk_ok} | missing/empty: {disk_missing} ({miss_frac*100:.1f}% of grid)",
          f"- total spend (this invocation): ${sum(spend.values()):.4f} (hard stop ${MAX_SPEND_USD:.0f})",
          f"- spend by provider: " + ", ".join(f"{k}=${v:.4f}" for k, v in spend.items()),
          f"- hard-stop (\\$300) tripped: {stop}", f"- raw corpus SHA-256: {digest}"]
    SPEND_PATH.write_text("\n".join(sr))
    print("\n".join(sr))
    print(f"\n[B1] run folder: {RUN_DIR.name}")
    print(f"[B1] MANIFEST_RAW.sha256 = {digest}  ({disk_ok} live / {disk_missing} missing on disk)")
    if miss_frac > MISSINGNESS_STOP_FRAC:
        print(f"\n[B1] *** MISSINGNESS {miss_frac*100:.1f}% > {MISSINGNESS_STOP_FRAC*100:.0f}% — "
              f"STOP per one-run rule. Do NOT patch or re-collect. Return the tarball + this report "
              f"and await instruction (analysis proceeds on the live cells; missing is a finding). ***")
    print("[B1] ONE-RUN RULE now in force: no cell is ever re-collected.")


if __name__ == "__main__":
    sys.exit(main())
