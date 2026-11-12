"""Builds outputs/showcase.html: the three tools as one executive narrative for a
Retail Development leader. Every number is computed by the tools at build time."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in ("", "01_investment_prioritiser", "02_store_economics", "03_review_pack"):
    sys.path.insert(0, str(ROOT / p))

from common import design as D  # noqa: E402
import economics as E  # noqa: E402
import prioritiser as P  # noqa: E402
import review_pack as RP  # noqa: E402
import generate_data  # noqa: E402


def gbp(v, signed=False):
    s = ("-" if v < 0 else "+") if signed else ("-" if v < 0 else "")
    a = abs(v)
    return f"{s}\u00a3{a/1e6:.1f}M" if a >= 1e5 else f"{s}\u00a3{a/1e3:.0f}K"


# ---------- project 1: prioritiser ----------
port = ROOT / "01_investment_prioritiser" / "portfolios" / "fy27.json"
pr = P.build(port)
util = pr["spend"] / pr["budget"]
deferred_capex = pr["capex_requested"] - pr["spend"]

funded_rows = "".join(
    f"<tr><td>{D.esc(s['name'])}</td><td>{D.esc(s['market'])}</td>"
    f"<td>{gbp(s['capex'])}</td><td>{gbp(s['npv'])}</td>"
    f"<td><span class='pill p-ok'>{'Must-do' if s['must_do'] else 'Fund'}</span></td></tr>"
    for s in pr["chosen"])
deferred_rows = "".join(
    f"<tr><td>{D.esc(s['name'])}</td><td>{D.esc(s['market'])}</td>"
    f"<td>{gbp(s['capex'])}</td><td>{gbp(s['npv'])}</td>"
    f"<td><span class='pill {'p-no' if s['npv']<=0 else 'p-chk'}'>{D.esc(pr['reasons'][s['id']])}</span></td></tr>"
    for s in pr["deferred"])

# bar chart: NPV of funded vs deferred candidates, in priority order
bar_rows = [(s["name"].split(" ")[0], round(s["npv"] / 1e6, 2), "ink", None) for s in pr["chosen"][:5]]
p1 = f"""
<section class="proj" id="p1"><div class="wrap">
<div class="label"><span class="n">01</span><span class="mono">Investment prioritiser</span></div>
<h2>Fund the portfolio, not the loudest request</h2>
<p class="answer">Across {len(pr['scored'])} candidate stores asking for {gbp(pr['capex_requested'])} of capital, the budget funds
<em>{len(pr['chosen'])} that capture {gbp(pr['npv_funded'])} of NPV</em> within {gbp(pr['budget'])} and {pr['max_slots']} delivery slots.
{gbp(deferred_capex)} of requests are deferred, with a reason attached to each.</p>
<div class="kpis">
 <div class="kpi"><div class="k">NPV funded</div><div class="v">{gbp(pr['npv_funded'])}</div><div class="c">from {len(pr['chosen'])} of {len(pr['scored'])} stores</div></div>
 <div class="kpi"><div class="k">CapEx committed</div><div class="v">{gbp(pr['spend'])}</div><div class="c">{util:.0%} of the {gbp(pr['budget'])} budget</div></div>
 <div class="kpi"><div class="k">Delivery slots</div><div class="v">{pr['slots_used']} of {pr['max_slots']}</div><div class="c">capacity, not just capital, is the constraint</div></div>
 <div class="kpi"><div class="k">Requests deferred</div><div class="v">{gbp(deferred_capex)}</div><div class="c">each with a stated reason</div></div>
</div>
<div class="grid2 wide">
 <div class="card"><h3>What gets funded, in priority order</h3><div class="sub">Priority blends value per pound of capital with strategic fit, feasibility and delivery capacity</div>
 <table class="m"><tr><th>Store</th><th>Market</th><th>CapEx</th><th>NPV</th><th>Call</th></tr>{funded_rows}</table></div>
 <div class="card"><h3>NPV of the funded set</h3><div class="sub">\u00a3M, by store</div>
 {D.hbars(bar_rows, lambda v: f'\u00a3{v:.1f}M', 'NPV of funded stores')}
 <p class="foot">Value is the NPV from the economics model (project 02), so the ranking and the business case use one set of numbers.</p></div>
</div>
<div class="card" style="margin-top:18px"><h3>Deferred, and why</h3><div class="sub">Nothing is dropped silently</div>
<table class="m"><tr><th>Store</th><th>Market</th><th>CapEx</th><th>NPV</th><th>Reason</th></tr>{deferred_rows}</table></div>
<div class="decision"><span class="mono">Decision</span><p>Approve the {len(pr['chosen'])}-store wave; carry the deferred city-format sites into the next delivery window rather than stretching the current one.</p></div>
</div></section>"""

# ---------- project 2: economics ----------
data = E.load_formats()
params = data["params"]
res = [E.evaluate(f, params) for f in data["formats"]]
# scenario: slow ramp
slow = [E.evaluate(f, {**params, "sales_ramp_mult": 0.80}) for f in data["formats"]]
flagship = next(r for r in res if r["format"] == "flagship")
popup = next(r for r in res if r["format"] == "popup_seasonal")
invest_n = sum(1 for r in res if r["verdict"][0] == "invest")

econ_bars = [(r["label"].split(" (")[0], round(r["npv"] / 1e6, 2),
              "ink" if r["npv"] > 0 else "ghost", None) for r in res]
# scenario comparison table
scen_rows = ""
for b, s in zip(res, slow):
    flip = " \u2192 " + s["verdict"][0].upper() if s["verdict"][0] != b["verdict"][0] else ""
    scen_rows += (f"<tr><td>{D.esc(b['label'])}</td><td>{gbp(b['npv'])}</td><td>{gbp(s['npv'])}</td>"
                  f"<td><span class='pill {'p-no' if s['verdict'][0]=='reject' else ('p-chk' if s['verdict'][0]=='review' else 'p-ok')}'>"
                  f"{s['verdict'][0].upper()}{flip}</span></td></tr>")

p2 = f"""
<section class="proj" id="p2"><div class="wrap">
<div class="label"><span class="n">02</span><span class="mono">Store economics</span></div>
<h2>Every business case, built the same way</h2>
<p class="answer">The flagship clears the hurdle at <em>{gbp(flagship['npv'])} NPV and a {flagship['payback_years']:.1f}-year payback</em>,
while the seasonal pop-up is a reject at {gbp(popup['npv'])}. {invest_n} of {len(res)} formats are an outright invest on the base case.</p>
<div class="kpis">
 <div class="kpi"><div class="k">Discount rate</div><div class="v">{params['discount_rate']:.0%}</div><div class="c">{params['horizon_years']}-year view</div></div>
 <div class="kpi"><div class="k">Payback hurdle</div><div class="v">{params['payback_hurdle_years']:.0f} yrs</div><div class="c">invest if cleared and NPV positive</div></div>
 <div class="kpi"><div class="k">Flagship NPV</div><div class="v">{gbp(flagship['npv'])}</div><div class="c">IRR {flagship['irr']:.0%}, ROIC {flagship['roic_horizon']:.1f}x</div></div>
 <div class="kpi"><div class="k">Invest verdicts</div><div class="v">{invest_n} of {len(res)}</div><div class="c">formats on the base case</div></div>
</div>
<div class="grid2 wide">
 <div class="card"><h3>NPV by format</h3><div class="sub">\u00a3M, {params['horizon_years']}-year, at the {params['discount_rate']:.0%} hurdle rate</div>
 {D.hbars(econ_bars, lambda v: f'\u00a3{v:.1f}M', 'NPV by format')}</div>
 <div class="card"><h3>Stress test: a slow sales ramp</h3><div class="sub">What happens if every format ramps to 80% of plan</div>
 <table class="m"><tr><th>Format</th><th>Base NPV</th><th>Slow ramp</th><th>Verdict</th></tr>{scen_rows}</table>
 <p class="foot">One toggle moves the whole portfolio. The compact format flips first, which tells you where the ramp assumption matters most.</p></div>
</div>
<div class="decision"><span class="mono">Decision</span><p>Hold the pop-up out of the capital plan and treat it as a marketing cost; underwrite the compact format only where the ramp assumption can be defended.</p></div>
</div></section>"""

# ---------- project 3: review pack ----------
generate_data.main()
RP.APPROVALS.write_text("{}")
df = RP.load()
s = RP.summarise(df)
bridge = RP.capex_bridge(df)
tot = s.sum()
open_var = int(tot.open_var)
capex_var = tot.capex_var
vol_tot = bridge.volume_effect.sum()
rate_tot = bridge.rate_effect.sum()
worst = s.open_var.idxmin()
over = bridge.rate_effect.idxmax()

review_rows = ""
for region, r in s.iterrows():
    review_rows += (f"<tr><td>{D.esc(region)}</td><td>{int(r.plan_openings)}</td><td>{int(r.actual_openings)}</td>"
                    f"<td>{int(r.open_var):+d}</td><td>{gbp(r.capex_var, True)}</td></tr>")

notes = RP.draft_commentary(s, bridge)
tags = ["Headline", "Biggest drag", "Cost watch", "Pattern", "Review"]
note_items = "".join(
    f"<li><b>{t}</b>{D.esc(n.split(': ', 1)[1] if ': ' in n else n)}</li>"
    for t, n in zip(tags, notes))

p3 = f"""
<section class="proj" id="p3"><div class="wrap">
<div class="label"><span class="n">03</span><span class="mono">Quarterly review</span></div>
<h2>The review that writes its own first draft</h2>
<p class="answer">{int(tot.actual_openings)} stores opened against a plan of {int(tot.plan_openings)} ({open_var:+d}), and the
{gbp(capex_var, True)} CapEx variance is <em>mostly phasing, not saving</em>: slower openings, not cheaper stores.</p>
<div class="banner draft"><span>DRAFT \u00b7 figures computed, causes are hypotheses until a reviewer approves</span><span class="hash">locked until sign-off</span></div>
<div class="kpis">
 <div class="kpi"><div class="k">Openings vs plan</div><div class="v">{int(tot.actual_openings)} of {int(tot.plan_openings)}</div><div class="c"><span class="down">{open_var:+d}</span> this quarter</div></div>
 <div class="kpi"><div class="k">CapEx variance</div><div class="v">{gbp(capex_var, True)}</div><div class="c">{gbp(tot.actual_capex)} vs {gbp(tot.plan_capex)} plan</div></div>
 <div class="kpi"><div class="k">Volume effect</div><div class="v">{gbp(vol_tot, True)}</div><div class="c">{worst} slipped the most</div></div>
 <div class="kpi"><div class="k">Cost-per-store effect</div><div class="v">{gbp(rate_tot, True)}</div><div class="c">{over} ran hot on fit-out</div></div>
</div>
<div class="grid2 wide">
 <div class="card"><h3>Openings and CapEx vs plan</h3><div class="sub">By region, this quarter</div>
 <table class="m"><tr><th>Region</th><th>Plan</th><th>Actual</th><th>Var</th><th>CapEx var</th></tr>{review_rows}</table></div>
 <div class="card"><h3>CapEx variance: phasing vs cost</h3><div class="sub">Volume effect vs cost-per-store effect, \u00a3M</div>
 {D.waterfall('Plan', round(tot.plan_capex/1e6,1), [('Fewer opens', round(vol_tot/1e6,1)), ('Cost per store', round(rate_tot/1e6,1))], 'Actual', lambda v, sg=False: (('+' if v>=0 else '-') if sg else ('-' if v<0 else ''))+f'\u00a3{abs(v):.1f}M', 'CapEx bridge')}
 <p class="foot">The split matters: phasing defers capital to next year; a cost-per-store overrun is a problem to fix before the next wave.</p></div>
</div>
<div class="card" style="margin-top:18px"><h3>What changed this quarter</h3><div class="sub">Drafted from the bridge; every number comes from the data, every cause is a hypothesis</div>
<ul class="notes">{note_items}</ul></div>
<div class="decision"><span class="mono">Decision</span><p>Approve to circulate; direct the cost review at {over} and the delivery review at {worst}. Leadership reviews the signed pack, not the draft.</p></div>
</div></section>"""

cover = f"""
<header class="cover"><div class="wrap">
<div class="mono">Retail development \u00b7 portfolio strategy and planning</div>
<h1>The numbers behind where a retailer opens next. Built with AI, signed off by a person.</h1>
<p class="lead">Three working tools for a store investment portfolio: how to prioritise capital across candidate stores, how to build each store's economics the same way, and how to review the portfolio against plan.</p>
<div class="heads">
 <div class="head"><b>{gbp(pr['npv_funded'])}</b><span>NPV funded from {len(pr['chosen'])} of {len(pr['scored'])} candidate stores</span></div>
 <div class="head"><b>{invest_n} of {len(res)}</b><span>store formats that clear the investment hurdle</span></div>
 <div class="head"><b>{gbp(capex_var, True)}</b><span>CapEx variance explained by phasing, not saving</span></div>
</div>
<div class="byline">Zubair Sohail \u00b7 how I think AI belongs in a planning function: the machine does the arithmetic and the first draft, a named person owns the judgment \u00b7 illustrative and public data only</div>
</div></header>
<nav class="toc"><div class="wrap"><a href="#p1">01 Investment prioritiser</a><a href="#p2">02 Store economics</a><a href="#p3">03 Quarterly review</a></div></nav>"""

foot = """<footer><div class="wrap">Built with AI as a coding partner, the way I believe AI belongs in a planning function: it does the arithmetic and the first draft, and a named person owns the judgment. Every figure on this page is generated by the tools at build time from illustrative data, and the tests check the finance maths (NPV, IRR, payback, the CapEx bridge) against hand calculations. Nothing here is drawn from any employer's confidential data.</div></footer>"""

out = ROOT / "outputs" / "showcase.html"
out.write_text(D.page("Retail portfolio strategy and planning", cover + p1 + p2 + p3 + foot))
# also write index.html so GitHub Pages serves it at the folder root
(ROOT / "outputs" / "index.html").write_text((ROOT / "outputs" / "showcase.html").read_text())
print("Saved", out, out.stat().st_size // 1024, "KB")
