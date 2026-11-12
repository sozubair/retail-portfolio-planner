"""Store development economics model.

Turns the inputs behind a store investment -- fit-out capital, rent, staffing and
other operating cost, a sales ramp, and a discount rate -- into the numbers a
leader decides on: NPV, payback, IRR and return on invested capital, by format.

Nothing here is retail-confidential. The assumptions are illustrative and set in
formats.json; the maths is standard corporate finance. The point is the method:
every output traces back to an input you can see and change.

Usage:
    python economics.py                 # all formats, base case
    python economics.py --format flagship --sales-ramp 0.85   # scenario toggle
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def npv(rate, cashflows):
    """cashflows[0] is year 0 (the capital outflow)."""
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(cashflows))


def irr(cashflows, lo=-0.9, hi=5.0):
    """Bisection IRR. Returns None if there is no sign change in range."""
    def f(r):
        return npv(r, cashflows)
    if f(lo) * f(hi) > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(lo) * f(mid) <= 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def payback_years(cashflows):
    """Simple payback: first year cumulative cash turns positive, interpolated."""
    cum = 0.0
    for t, cf in enumerate(cashflows):
        prev = cum
        cum += cf
        if cum >= 0 and t > 0:
            # interpolate within the year
            return (t - 1) + (-prev) / cf if cf else float(t)
    return None


def build_cashflows(f, horizon, sales_ramp_mult=1.0, rent_mult=1.0):
    """Return the yearly free cash flows for one store format.

    Year 0 is -capex. Years 1..horizon are contribution less operating cost.
    Contribution = sales * gross_margin. Sales climb a ramp to a mature level.
    """
    capex = f["capex_fitout"] + f["capex_fixtures"]
    mature_sales = f["mature_annual_sales"]
    ramp = [min(r * sales_ramp_mult, 1.0) for r in f["sales_ramp_pct_of_mature"]]
    gm = f["gross_margin_pct"]
    rent = f["annual_rent"] * rent_mult
    other_opex = f["annual_staff_cost"] + f["annual_other_opex"]
    cfs = [-capex]
    for t in range(1, horizon + 1):
        pct = ramp[t - 1] if t - 1 < len(ramp) else ramp[-1]
        sales = mature_sales * pct
        contribution = sales * gm
        fcf = contribution - rent - other_opex
        cfs.append(fcf)
    # terminal value: capitalise the final-year FCF as a perpetuity-lite (one extra year),
    # kept deliberately simple and conservative
    return cfs


def evaluate(f, params):
    horizon = params["horizon_years"]
    rate = params["discount_rate"]
    cfs = build_cashflows(f, horizon,
                          sales_ramp_mult=params.get("sales_ramp_mult", 1.0),
                          rent_mult=params.get("rent_mult", 1.0))
    capex = -cfs[0]
    store_npv = npv(rate, cfs)
    store_irr = irr(cfs)
    pb = payback_years(cfs)
    total_fcf = sum(cfs[1:])
    roic = total_fcf / capex if capex else None
    mature_fcf = cfs[-1]
    return {
        "format": f["format"],
        "label": f["label"],
        "capex": capex,
        "mature_annual_sales": f["mature_annual_sales"],
        "mature_annual_fcf": mature_fcf,
        "npv": store_npv,
        "irr": store_irr,
        "payback_years": pb,
        "roic_horizon": roic,
        "cashflows": cfs,
        "verdict": verdict(store_npv, pb, params),
    }


def verdict(store_npv, pb, params):
    hurdle_pb = params["payback_hurdle_years"]
    if store_npv <= 0:
        return ("reject", "NPV is negative at the hurdle rate")
    if pb is None or pb > hurdle_pb:
        return ("review", f"NPV positive but payback above the {hurdle_pb}-year hurdle")
    return ("invest", f"NPV positive and payback within {hurdle_pb} years")


def load_formats():
    return json.loads((ROOT / "formats.json").read_text())


def gbp(x):
    a = abs(x)
    s = "-" if x < 0 else ""
    if a >= 1e6:
        return f"{s}\u00a3{a/1e6:,.2f}M"
    return f"{s}\u00a3{a/1e3:,.0f}K"


def render(results, params):
    L = [f"# Store development economics ({params['horizon_years']}-year view, "
         f"{params['discount_rate']:.0%} discount rate)", ""]
    if params.get("sales_ramp_mult", 1.0) != 1.0 or params.get("rent_mult", 1.0) != 1.0:
        L.append(f"_Scenario: sales ramp x{params.get('sales_ramp_mult',1.0):.2f}, "
                 f"rent x{params.get('rent_mult',1.0):.2f}._\n")
    L += ["| Format | CapEx | Mature sales | NPV | IRR | Payback | ROIC | Verdict |",
          "|---|---:|---:|---:|---:|---:|---:|---|"]
    for r in results:
        irr_txt = f"{r['irr']:.0%}" if r["irr"] is not None else "n/a"
        pb_txt = f"{r['payback_years']:.1f} yrs" if r["payback_years"] else "never"
        L.append(f"| {r['label']} | {gbp(r['capex'])} | {gbp(r['mature_annual_sales'])} | "
                 f"{gbp(r['npv'])} | {irr_txt} | {pb_txt} | {r['roic_horizon']:.1f}x | "
                 f"{r['verdict'][0].upper()} |")
    L.append("")
    L.append("Verdict rule: invest if NPV positive and payback within the hurdle; "
             "review if NPV positive but slow to pay back; reject if NPV negative. "
             "Every figure traces back to an input in formats.json.")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", default=None, help="evaluate one format by key")
    ap.add_argument("--sales-ramp", type=float, default=1.0,
                    help="multiplier on the sales ramp, e.g. 0.85 for a slow ramp")
    ap.add_argument("--rent", type=float, default=1.0, help="multiplier on rent")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    data = load_formats()
    params = dict(data["params"])
    params["sales_ramp_mult"] = a.sales_ramp
    params["rent_mult"] = a.rent
    formats = data["formats"]
    if a.format:
        formats = [f for f in formats if f["format"] == a.format]
    results = [evaluate(f, params) for f in formats]
    md = render(results, params)
    out = Path(a.out) if a.out else ROOT.parent / "outputs" / "store_economics.md"
    out.write_text(md)
    print(md)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
