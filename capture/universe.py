"""Emit the stratified 100-firm S&P 500 pilot universe -> data/universe.csv.

Current S&P 500 constituents (public membership), stratified across the 11 GICS
sectors. Size stratification is handled downstream from captured market cap.
Survivorship bias (current constituents) is acknowledged and flagged in the
report as a full-study fix (point-in-time constituents).
"""
from __future__ import annotations
import csv
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]

# 100 names across 11 GICS sectors (public S&P 500 membership + GICS classification).
UNIVERSE: dict[str, list[str]] = {
    "Information Technology": ["AAPL","MSFT","NVDA","AVGO","CRM","ORCL","ADBE","AMD","CSCO","ACN","INTC"],
    "Financials":            ["JPM","BAC","WFC","GS","MS","C","AXP","SCHW","BLK","SPGI","CB"],
    "Health Care":           ["UNH","JNJ","LLY","PFE","ABBV","MRK","TMO","ABT","DHR","BMY","AMGN"],
    "Consumer Discretionary":["AMZN","TSLA","HD","MCD","NKE","LOW","SBUX","BKNG","TJX","GM"],
    "Communication Services":["GOOGL","META","NFLX","DIS","CMCSA","VZ","T","TMUS","CHTR"],
    "Industrials":           ["CAT","BA","HON","UNP","GE","RTX","DE","LMT","UPS","ETN"],
    "Consumer Staples":      ["PG","KO","PEP","COST","WMT","MDLZ","CL","MO","TGT"],
    "Energy":                ["XOM","CVX","COP","SLB","EOG","MPC","PSX","OXY"],
    "Utilities":             ["NEE","DUK","SO","D","AEP","EXC","XEL"],
    "Materials":             ["LIN","SHW","FCX","NEM","APD","ECL","NUE"],
    "Real Estate":           ["PLD","AMT","EQIX","SPG","O","CCI","PSA"],
}


def main() -> int:
    rows = [(t, sec) for sec, ts in UNIVERSE.items() for t in ts]
    assert len(rows) == 100, f"expected 100, got {len(rows)}"
    assert len({t for t, _ in rows}) == 100, "duplicate tickers"
    out = _HERE / "data" / "universe.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ticker", "gics_sector"])
        w.writerows(rows)
    print(f"wrote {len(rows)} firms across {len(UNIVERSE)} sectors -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
