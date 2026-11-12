"""Quarterly portfolio review pack.

A quarterly Retail Development review that writes its own first draft and cannot be
circulated until a named person approves it. It bridges actual store openings and
CapEx against plan, splits the variance into its drivers (slippage in the number of
openings vs cost per store), drafts the "what changed" commentary as hypotheses,
and stays marked DRAFT until a reviewer signs off. Approval is logged with a hash
of the content, so later edits are visible.

Usage:
    python review_pack.py                       # build the draft
    python review_pack.py --approve "Name"      # sign it off
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "portfolio_quarter.csv"
APPROVALS = ROOT / "data" / "approvals.json"


def load():
    return pd.read_csv(DATA)


def summarise(df):
    g = df.groupby("region").agg(
        plan_openings=("plan_openings", "sum"),
        actual_openings=("actual_openings", "sum"),
        plan_capex=("plan_capex", "sum"),
        actual_capex=("actual_capex", "sum"),
    )
    g["open_var"] = g.actual_openings - g.plan_openings
    g["capex_var"] = g.actual_capex - g.plan_capex
    return g


def capex_bridge(df):
    """Split total CapEx variance into a volume effect and a cost-per-store effect.

    volume effect = (actual openings - plan openings) * plan cost per store
    rate effect   = (actual cost per store - plan cost per store) * actual openings
    These two sum to the total CapEx variance (standard price/volume bridge).
    """
    rows = []
    for region, r in summarise(df).iterrows():
        plan_cps = r.plan_capex / r.plan_openings if r.plan_openings else 0
        actual_cps = r.actual_capex / r.actual_openings if r.actual_openings else 0
        vol = (r.actual_openings - r.plan_openings) * plan_cps
        rate = (actual_cps - plan_cps) * r.actual_openings
        rows.append({"region": region, "volume_effect": vol, "rate_effect": rate,
                     "plan_cps": plan_cps, "actual_cps": actual_cps,
                     "total_var": r.capex_var})
    return pd.DataFrame(rows).set_index("region")


def draft_commentary(s, bridge):
    lines = []
    tot_open_var = int(s.open_var.sum())
    tot_capex_var = s.capex_var.sum()
    lines.append(
        f"Headline: {int(s.actual_openings.sum())} stores opened against a plan of "
        f"{int(s.plan_openings.sum())} ({tot_open_var:+d}), and CapEx of {gbp(s.actual_capex.sum())} "
        f"against {gbp(s.plan_capex.sum())} ({gbp(tot_capex_var, True)}).")
    worst = s.open_var.idxmin()
    if s.loc[worst, "open_var"] < 0:
        lines.append(
            f"Biggest drag: {worst} opened {int(-s.loc[worst,'open_var'])} fewer stores than plan. "
            f"Hypothesis: delivery slippage, confirm against the site-readiness tracker.")
    over = bridge.rate_effect.idxmax()
    if bridge.loc[over, "rate_effect"] > 0:
        lines.append(
            f"Cost watch: in {over}, cost per store ran {gbp(bridge.loc[over,'actual_cps']-bridge.loc[over,'plan_cps'], True)} "
            f"above plan ({gbp(bridge.loc[over,'rate_effect'], True)} of variance). "
            f"Hypothesis: fit-out inflation or scope creep, not volume.")
    # shared pattern: is the CapEx underspend mostly volume (good for the year) or rate?
    vol_tot = bridge.volume_effect.sum()
    rate_tot = bridge.rate_effect.sum()
    driver = "fewer openings" if abs(vol_tot) > abs(rate_tot) else "cost per store"
    lines.append(
        f"Pattern: the {gbp(tot_capex_var, True)} CapEx variance is mostly {driver} "
        f"(volume {gbp(vol_tot, True)}, rate {gbp(rate_tot, True)}). "
        f"That points to {'phasing, so the capital is deferred not saved' if driver=='fewer openings' else 'a unit-cost problem to fix before the next wave'}.")
    lines.append("Review: approve to circulate; until then this is a draft and the causes are hypotheses.")
    return lines


def gbp(x, signed=False):
    a = abs(x)
    sign = ("-" if x < 0 else "+") if signed else ("-" if x < 0 else "")
    if a >= 1e6:
        return f"{sign}\u00a3{a/1e6:,.2f}M"
    return f"{sign}\u00a3{a/1e3:,.0f}K"


def content_hash(s, bridge):
    payload = s.round(2).to_json() + bridge.round(2).to_json()
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def approvals():
    if APPROVALS.exists():
        return json.loads(APPROVALS.read_text())
    return {}


def build():
    df = load()
    s = summarise(df)
    bridge = capex_bridge(df)
    h = content_hash(s, bridge)
    appr = approvals().get(h)
    status = f"APPROVED by {appr['by']} on {appr['on']}" if appr else "DRAFT (not approved)"
    md = render(s, bridge, status, h)
    out = ROOT.parent / "outputs" / "portfolio_review.md"
    out.write_text(md)
    return out, md, status


def render(s, bridge, status, h):
    L = [f"# Quarterly portfolio review \u2014 {status}", "",
         f"_Content fingerprint: {h}. Figures are computed; causes are hypotheses until approved._", "",
         "## Openings and CapEx vs plan", "",
         "| Region | Plan openings | Actual | Var | Plan CapEx | Actual CapEx | Var |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    for region, r in s.iterrows():
        L.append(f"| {region} | {int(r.plan_openings)} | {int(r.actual_openings)} | {int(r.open_var):+d} | "
                 f"{gbp(r.plan_capex)} | {gbp(r.actual_capex)} | {gbp(r.capex_var, True)} |")
    tot = s.sum()
    L.append(f"| **Total** | **{int(tot.plan_openings)}** | **{int(tot.actual_openings)}** | "
             f"**{int(tot.open_var):+d}** | **{gbp(tot.plan_capex)}** | **{gbp(tot.actual_capex)}** | "
             f"**{gbp(tot.capex_var, True)}** |")
    L += ["", "## CapEx variance bridge (volume vs cost per store)", "",
          "| Region | Volume effect | Rate effect | Total |", "|---|---:|---:|---:|"]
    for region, r in bridge.iterrows():
        L.append(f"| {region} | {gbp(r.volume_effect, True)} | {gbp(r.rate_effect, True)} | {gbp(r.total_var, True)} |")
    L += ["", "## What changed this quarter", ""]
    L += [f"* {line}" for line in draft_commentary(s, bridge)]
    return "\n".join(L)


def approve(name):
    df = load()
    s = summarise(df)
    bridge = capex_bridge(df)
    h = content_hash(s, bridge)
    from datetime import date
    data = approvals()
    data[h] = {"by": name, "on": date.today().isoformat()}
    APPROVALS.write_text(json.dumps(data, indent=2))
    print(f"Approved fingerprint {h} by {name}. Re-run build to see it circulate-ready.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve", default=None, help="reviewer name to sign off the current content")
    a = ap.parse_args()
    if a.approve:
        approve(a.approve)
        return
    out, md, status = build()
    print(md)
    print(f"\n[{status}]  Saved {out}")


if __name__ == "__main__":
    main()
