"""Store investment prioritiser.

The portfolio problem a Retail Development leader actually faces: more candidate
store projects than capital or delivery capacity can support. This tool scores
each candidate on value, strategic fit, feasibility and delivery capacity, then
chooses the set that maximises value within a CapEx budget and a delivery-slot
limit -- and shows what it left out and why.

Value is not a made-up score: it is the NPV from the store economics model (tool
02), so prioritisation and the business case use the same numbers.

Usage:
    python prioritiser.py portfolios/fy27.json
    python prioritiser.py portfolios/fy27.json --budget 9000000 --max-slots 6
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "02_store_economics"))
sys.path.insert(0, str(ROOT.parent))
import economics as E  # noqa: E402
from common.llm import polish  # noqa: E402

# weights for the strategic score (0-1 inputs in the candidate file)
WEIGHTS = {"strategic_fit": 0.40, "feasibility": 0.35, "capacity_fit": 0.25}


def strategic_score(c):
    return sum(c[k] * w for k, w in WEIGHTS.items())


def score_candidate(c, formats, params):
    f = formats[c["format"]]
    econ = E.evaluate(f, params)
    # candidate-level overrides let one site differ from its format archetype
    capex = c.get("capex_override", econ["capex"])
    npv = econ["npv"] * c.get("npv_mult", 1.0)
    strat = strategic_score(c)
    # blended priority: value per pound of capital, tilted by strategic score
    value_density = npv / capex if capex else 0
    priority = value_density * (0.5 + strat)  # strat in [0,1] scales density 0.5x-1.5x
    return {
        "id": c["id"],
        "name": c["name"],
        "market": c["market"],
        "format": c["format"],
        "format_label": f["label"],
        "capex": capex,
        "npv": npv,
        "value_density": value_density,
        "strategic_fit": c["strategic_fit"],
        "feasibility": c["feasibility"],
        "capacity_fit": c["capacity_fit"],
        "strategic_score": strat,
        "priority": priority,
        "must_do": c.get("must_do", False),
        "econ_verdict": econ["verdict"][0],
    }


def select(scored, budget, max_slots):
    """Greedy-by-priority selection under a CapEx budget and a delivery-slot cap.

    Greedy on value density is optimal-ish for this fractional-free knapsack and,
    importantly, explainable: leaders can see the ranking. Must-do projects are
    funded first (committed/compliance), then the rest by priority.
    """
    must = [s for s in scored if s["must_do"]]
    rest = sorted((s for s in scored if not s["must_do"]),
                  key=lambda s: s["priority"], reverse=True)
    chosen, spend, slots = [], 0.0, 0
    reasons = {}
    for s in must:
        chosen.append(s); spend += s["capex"]; slots += 1
        reasons[s["id"]] = "committed / must-do"
    for s in rest:
        if s["npv"] <= 0:
            reasons[s["id"]] = "NPV not positive"
            continue
        if slots >= max_slots:
            reasons[s["id"]] = "no delivery slot left"
            continue
        if spend + s["capex"] > budget:
            reasons[s["id"]] = "would breach CapEx budget"
            continue
        chosen.append(s); spend += s["capex"]; slots += 1
        reasons[s["id"]] = "funded"
    deferred = [s for s in scored if reasons.get(s["id"]) not in ("funded", "committed / must-do")]
    return chosen, deferred, reasons, spend, slots


def build(path, budget=None, max_slots=None):
    port = json.loads(Path(path).read_text())
    econ = E.load_formats()
    params = econ["params"]
    formats = {f["format"]: f for f in econ["formats"]}
    budget = budget if budget is not None else port["capex_budget"]
    max_slots = max_slots if max_slots is not None else port["delivery_slots"]
    scored = [score_candidate(c, formats, params) for c in port["candidates"]]
    chosen, deferred, reasons, spend, slots = select(scored, budget, max_slots)
    return {
        "name": port["name"],
        "budget": budget,
        "max_slots": max_slots,
        "scored": sorted(scored, key=lambda s: s["priority"], reverse=True),
        "chosen": sorted(chosen, key=lambda s: s["priority"], reverse=True),
        "deferred": sorted(deferred, key=lambda s: s["priority"], reverse=True),
        "reasons": reasons,
        "spend": spend,
        "slots_used": slots,
        "npv_funded": sum(s["npv"] for s in chosen),
        "npv_total": sum(s["npv"] for s in scored if s["npv"] > 0),
        "capex_requested": sum(s["capex"] for s in scored),
    }


def render(r):
    g = E.gbp
    L = [f"# Store investment prioritisation: {r['name']}", "",
         f"**Recommendation.** Fund {len(r['chosen'])} of {len(r['scored'])} candidate "
         f"stores for {g(r['spend'])} of the {g(r['budget'])} CapEx budget "
         f"({r['slots_used']} of {r['max_slots']} delivery slots), capturing "
         f"{g(r['npv_funded'])} of NPV. Demand for capital was {g(r['capex_requested'])}, "
         f"so {g(r['capex_requested']-r['spend'])} of requests were deferred.", "",
         "## Funded, in priority order", "",
         "| Rank | Store | Market | Format | CapEx | NPV | Strategic | Why |",
         "|---|---|---|---|---:|---:|---:|---|"]
    for i, s in enumerate(r["chosen"], 1):
        L.append(f"| {i} | {s['name']} | {s['market']} | {s['format_label']} | {g(s['capex'])} | "
                 f"{g(s['npv'])} | {s['strategic_score']:.2f} | {r['reasons'][s['id']]} |")
    L += ["", "## Deferred", "",
          "| Store | Market | Format | CapEx | NPV | Strategic | Reason |",
          "|---|---|---|---:|---:|---:|---|"]
    for s in r["deferred"]:
        L.append(f"| {s['name']} | {s['market']} | {s['format_label']} | {g(s['capex'])} | "
                 f"{g(s['npv'])} | {s['strategic_score']:.2f} | {r['reasons'][s['id']]} |")
    L += ["", "Method: value is the NPV from the store economics model, so the ranking and the "
          "business case use the same numbers. Priority blends value per pound of capital with a "
          "strategic score (fit, feasibility, delivery capacity). Must-do projects are funded first, "
          "then the rest by priority until the budget or delivery slots run out."]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("portfolio")
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--max-slots", type=int, default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    r = build(a.portfolio, a.budget, a.max_slots)
    md = render(r)
    better = polish("Tighten this investment recommendation for a retail leader. "
                    "Keep every number exactly as written. Do not add claims.", md)
    md = better or md
    out = Path(a.out) if a.out else ROOT.parent / "outputs" / "prioritisation.md"
    out.write_text(md)
    print(md)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
