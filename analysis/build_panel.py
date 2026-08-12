"""B2 — deterministic panel build (no network). Reads the frozen run corpus, applies
the 3 A8 parse rules to every completion, coarsens credit letters to notch/band/IG-HY,
and writes panel.parquet (item x spec x seed x parse-rule, with the granularity columns).
Also panel_quality_report.md (missingness, dead-cell census, strict-vs-lenient, scale-usage
entropy) and MANIFEST_PANEL.sha256. Raw failing all 3 rules is logged, never edited.
"""
from __future__ import annotations
import json, glob, re, collections, hashlib, math
from pathlib import Path
import pandas as pd

PB = Path(__file__).resolve().parents[1]
RUN = PB / "data" / "raw" / "main" / "run_20260707_185649"          # the frozen Phase B run
RAWG = sorted(glob.glob(str(RUN / "raw" / "*.json")))
OUT = PB / "data" / "panel"; OUT.mkdir(exist_ok=True)
RS = json.load(open(PB / "data" / "frozen" / "main" / "rating_scale.json"))

LETTERS = RS["letter_scale"]; LSET = set(LETTERS)
L2NOTCH = RS["letter_to_notch_collapsed"]; L2BAND = RS["letter_to_band"]; L2IGHY = RS["letter_to_ig_hy"]
DIRL = ["BUY", "HOLD", "SELL"]
EXCLUDE = {("xai", "prior")}     # documented dead cell (deviations A4)
AXES = ["A1_provider", "A2_version", "A3_temperature", "A4_paraphrase", "A5_format", "A6_fewshot", "A7_presentation"]

# ordered letter tokens for regex (longest first so 'AAA' matches before 'AA'/'A')
_LTOK = sorted(LETTERS + ["D"], key=len, reverse=True)
_LRE = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(t) for t in _LTOK) + r")(?![A-Za-z0-9])")


def _clean_json(txt):
    t = txt.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", t).strip()
    t = t.lstrip("{").rjust(len(t.lstrip("{")) + 1, "{")  # normalise accidental {{
    i = t.find("{")
    if i < 0:
        return None
    try:
        obj, _ = json.JSONDecoder().raw_decode(t[i:])
        return obj
    except Exception:
        return None


def _valid_letter(x, tolerant=False):
    if x is None:
        return None
    x = str(x).strip().upper().replace(" ", "")
    if x in LSET:
        return x
    if tolerant and x == "D":
        return "C"        # EMS 'D' -> 'C' on the AAA..C scale (rating_scale note)
    return None


def parse_credit(txt, fmt, rule):
    if not txt:
        return None
    if rule == "strict":
        if fmt == "json":
            o = _clean_json(txt)
            return _valid_letter(o.get("decision")) if isinstance(o, dict) else None
        m = re.search(r"^\s*(?:DECISION|RATING)\s*:\s*([A-D]{1,3}[+-]?)\s*$", txt, re.I | re.M)
        return _valid_letter(m.group(1)) if m else None
    # lenient / tolerant
    o = _clean_json(txt)
    if isinstance(o, dict):
        v = _valid_letter(o.get("decision"), rule == "tolerant")
        if v:
            return v
    m = re.search(r"(?:DECISION|RATING)\s*:?\s*\**([A-D]{1,3}[+-]?)", txt, re.I)
    if m:
        v = _valid_letter(m.group(1), rule == "tolerant")
        if v:
            return v
    toks = [_valid_letter(t, rule == "tolerant") for t in _LRE.findall(txt)]
    toks = [t for t in toks if t]
    return toks[-1] if toks else None      # last valid letter mentioned


def parse_dir(txt, fmt, rule):
    if not txt:
        return None
    if rule == "strict":
        if fmt == "json":
            o = _clean_json(txt)
            d = str(o.get("decision", "")).strip().upper() if isinstance(o, dict) else ""
            return d if d in DIRL else None
        m = re.search(r"^\s*DECISION\s*:\s*([A-Za-z]+)\s*$", txt, re.I | re.M)
        return m.group(1).upper() if (m and m.group(1).upper() in DIRL) else None
    o = _clean_json(txt)
    if isinstance(o, dict):
        d = str(o.get("decision", "")).strip().upper()
        if d in DIRL:
            return d
    m = re.search(r"DECISION\s*:?\s*\**([A-Za-z]+)", txt, re.I)
    if m and m.group(1).upper() in DIRL:
        return m.group(1).upper()
    hits = [l for l in DIRL if re.search(r"\b" + l + r"\b", txt.upper())]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        pos = {l: txt.upper().rfind(l) for l in hits}
        return max(pos, key=pos.get)
    return None


def main():
    rows = []
    allrec = []          # for quality census (includes missing/dead)
    for p in RAWG:
        d = json.load(open(p))
        allrec.append(d)
        if (d.get("provider"), d.get("version")) in EXCLUDE or not d.get("ok"):
            continue
        fam = d["family"]; fmt = d["axes"]["A5_format"]; meta = d.get("call_meta") or {}
        base = dict(item_id=d["item_id"], spec_id=d["spec_id"], seed=d["seed"], family=fam,
                    provider=d["provider"], version=d["version"], model=d["model"],
                    benchmark=d["benchmark_label"],
                    requested_temp=float(d.get("requested_temperature")),
                    temp_applied=bool(meta.get("temperature_applied", d.get("temperature_applied", True))),
                    effective_temp=d.get("effective_temperature"),
                    **{a: d["axes"][a] for a in AXES if a != "A1_provider"}, A1_provider=d["provider"])
        for rule in ["strict", "lenient", "tolerant"]:
            r = dict(base); r["parse_rule"] = rule
            if fam == "credit_health":
                let = parse_credit(d["raw_response"], fmt, rule)
                r["parsed"] = let is not None
                r["dec_letter"] = let
                r["dec_notch"] = L2NOTCH.get(let) if let else None
                r["dec_band"] = L2BAND.get(let) if let else None
                r["dec_ighy"] = L2IGHY.get(let) if let else None
                r["decision"] = let
                r["bench_band"] = d["benchmark_label"]     # Paper 2 SAFE/WATCH/DISTRESS
            else:
                dec = parse_dir(d["raw_response"], fmt, rule)
                r["parsed"] = dec is not None
                r["decision"] = dec
                r["dec_letter"] = r["dec_notch"] = r["dec_band"] = r["dec_ighy"] = None
                r["bench_band"] = d["benchmark_label"]     # BUY/SELL
            rows.append(r)
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / "panel.parquet", index=False)

    # ---- quality report ----
    q = []
    cells = collections.Counter(); okc = collections.Counter(); misc = collections.Counter()
    for d in allrec:
        c = f"{d['provider']}/{d['version']}"; cells[c] += 1
        (okc if d.get("ok") else misc)[c] += 1
    # scale-usage entropy (credit, lenient parse) — how many of 21 letters used
    cred = df[(df.family == "credit_health") & (df.parse_rule == "lenient") & df.dec_letter.notna()]
    def entropy(series):
        vc = series.value_counts(normalize=True)
        H = -sum(pp * math.log2(pp) for pp in vc if pp > 0)
        return round(H, 3), int(series.nunique())
    Hall, nall = entropy(cred.dec_letter)
    prov_ent = {pr: entropy(g.dec_letter) for pr, g in cred.groupby("provider")}
    # strict vs lenient disagreement
    piv = df.pivot_table(index=["item_id", "spec_id", "seed", "family"], columns="parse_rule",
                         values="decision", aggfunc="first")
    both = piv.dropna(subset=["strict", "lenient"])
    disagree = float((both["strict"] != both["lenient"]).mean()) if len(both) else 0.0
    parse_rates = {r: round(float(df[df.parse_rule == r].parsed.mean()), 4) for r in ["strict", "lenient", "tolerant"]}
    all3fail = df.pivot_table(index=["item_id", "spec_id", "seed"], values="parsed", aggfunc="sum")
    n_all3fail = int((all3fail["parsed"] == 0).sum())

    q.append("# Phase B — Panel quality report")
    q.append("")
    q.append(f"- source run: `{RUN.name}` (MANIFEST_RAW `{open(RUN/'MANIFEST_RAW.sha256').read().strip()[:16]}`)")
    q.append(f"- panel rows: {len(df)} (item x spec x seed x 3 parse-rules; live cells only)")
    q.append(f"- ok cells used: {len(df)//3} | dead cell excluded: xai/prior grok-4.1-fast")
    q.append("")
    q.append("## Cell census (all raw incl. missing)")
    q.append("| cell | total | ok | missing |")
    q.append("|---|---|---|---|")
    for c in sorted(cells):
        q.append(f"| {c} | {cells[c]} | {okc[c]} | {misc[c]} |")
    q.append("")
    q.append("## Parse rates + strict-vs-lenient")
    q.append(f"- lenient {parse_rates['lenient']*100:.1f}% | strict {parse_rates['strict']*100:.1f}% | "
             f"tolerant {parse_rates['tolerant']*100:.1f}%")
    q.append(f"- strict-vs-lenient decision disagreement: {disagree*100:.2f}%")
    q.append(f"- cells failing ALL 3 parse rules (logged, not edited): {n_all3fail}")
    q.append("")
    q.append("## Scale-usage entropy (credit, 21-grade letter scale) — compression check")
    q.append(f"- overall: {nall} of 21 letters used; Shannon entropy {Hall} bits (max {round(math.log2(21),2)})")
    for pr, (H, n) in prov_ent.items():
        q.append(f"  - {pr}: {n}/21 letters, entropy {H} bits")
    q.append("")
    q.append("**Reading.** Low letter-count / low entropy = central-tendency compression; reported so that "
             "compression cannot be mistaken for stability in the granularity analysis (B3.7).")
    (OUT / "panel_quality_report.md").write_text("\n".join(q))

    # ---- hash ----
    h = hashlib.sha256()
    for f in ["panel.parquet", "panel_quality_report.md"]:
        h.update((OUT / f).read_bytes())
    h.update(Path(__file__).resolve().read_bytes())   # hash this script from its own (analysis/) location
    (OUT / "MANIFEST_PANEL.sha256").write_text(h.hexdigest() + "\n")
    print("panel rows:", len(df), "| parse (lenient):", parse_rates["lenient"],
          "| strict-vs-lenient disagree:", round(disagree, 4))
    print("scale usage: overall", nall, "/21 letters, entropy", Hall, "bits;", prov_ent)
    print("all-3-parse-fail cells:", n_all3fail)
    print("MANIFEST_PANEL:", h.hexdigest()[:16])


if __name__ == "__main__":
    main()
