"""Design system for executive-ready outputs.

Principles applied (sources in showcase/DESIGN.md):
* Answer first: every view opens with the conclusion, then the evidence.
* Numbers with context: every KPI shows its comparison (target, baseline, last week).
* Position and length encode quantities; labels sit on the data, no legends.
* Quiet neutrals everywhere, one accent for the thing to look at.
* Uncertainty is shown, not hidden: ranges appear wherever an estimate does.
"""
import base64
import html
from pathlib import Path

FONTS = Path(__file__).resolve().parent.parent / "showcase" / "fonts"

INK, INK2, MUTED = "#17153A", "#4B4966", "#8A8799"
PAPER, CARD, LINE = "#F6F2EA", "#FFFFFF", "#E6DFD2"
GOLD, YELLOW = "#B07A00", "#FFC83D"
GOOD, BAD, WARN, NEUTRAL = "#2E7D5B", "#C2412D", "#B7791F", "#CFC7B8"


def _font(name, fam, weight):
    p = FONTS / name
    if not p.exists():
        return ""
    b64 = base64.b64encode(p.read_bytes()).decode()
    return (f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,{b64}) format('woff2');"
            f"font-weight:{weight};font-display:swap}}")


def css():
    return (_font("inter.woff2", "Inter", "400 700") + _font("fraunces.woff2", "Fraunces", "400 700")
            + _font("mono.woff2", "JB Mono", "500") + f"""
:root{{--ink:{INK};--ink2:{INK2};--muted:{MUTED};--paper:{PAPER};--card:{CARD};--line:{LINE};
--gold:{GOLD};--yellow:{YELLOW};--good:{GOOD};--bad:{BAD};--warn:{WARN}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font:400 15px/1.55 Inter,system-ui,sans-serif;
font-feature-settings:'tnum' 1,'cv11' 1;-webkit-font-smoothing:antialiased}}
h1,h2,h3{{font-family:Fraunces,Georgia,serif;font-weight:500;letter-spacing:-.01em;margin:0}}
.mono{{font-family:'JB Mono',ui-monospace,monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase}}
.wrap{{max-width:1120px;margin:0 auto;padding:0 40px}}
.cover{{background:var(--ink);color:#fff;padding:72px 0 64px;position:relative;overflow:hidden}}
.cover:after{{content:'';position:absolute;right:-120px;top:-120px;width:420px;height:420px;border-radius:50%;
background:radial-gradient(circle,rgba(255,200,61,.28),rgba(255,200,61,0) 70%)}}
.cover .mono{{color:var(--yellow)}}
.cover h1{{font-size:50px;line-height:1.08;margin:18px 0 16px;max-width:960px}}
.cover p.lead{{font-size:18px;color:#C9C7DA;max-width:720px;margin:0}}
.heads{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:44px}}
.head{{border-top:1px solid rgba(255,255,255,.18);padding-top:16px}}
.head b{{display:block;font:500 40px/1 Fraunces,serif;color:#fff}}
.head span{{color:#C9C7DA;font-size:14px}}
.byline{{margin-top:40px;color:#9C9AB3;font-size:13px}}
nav.toc{{position:sticky;top:0;z-index:5;background:rgba(246,242,234,.92);backdrop-filter:blur(8px);
border-bottom:1px solid var(--line)}}
nav.toc .wrap{{display:flex;gap:28px;height:52px;align-items:center}}
nav.toc a{{color:var(--ink2);text-decoration:none;font-weight:500;font-size:14px}}
nav.toc a:hover{{color:var(--ink)}}
section.proj{{padding:64px 0 24px}}
.label{{display:flex;align-items:center;gap:12px;color:var(--gold)}}
.label .n{{font:500 13px 'JB Mono',monospace;border:1px solid var(--gold);border-radius:999px;padding:2px 10px}}
section.proj h2{{font-size:36px;margin:14px 0 10px}}
.answer{{font:400 22px/1.4 Fraunces,serif;color:var(--ink);max-width:880px;margin:0 0 28px}}
.answer em{{font-style:normal;background:linear-gradient(transparent 62%,rgba(255,200,61,.55) 62%)}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:22px}}
.kpi{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px}}
.kpi .k{{color:var(--muted);font-size:13px;font-weight:500}}
.kpi .v{{font:600 30px/1.15 Inter,sans-serif;letter-spacing:-.02em;margin:6px 0 4px}}
.kpi .c{{font-size:13px;color:var(--ink2)}}
.up{{color:var(--good);font-weight:600}}.down{{color:var(--bad);font-weight:600}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.grid2.wide{{grid-template-columns:1.6fr 1fr}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px 24px}}
.card h3{{font-size:19px;margin-bottom:4px}}
.card .sub{{color:var(--muted);font-size:13px;margin-bottom:12px}}
.steps{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0}}
.step{{border-top:2px solid var(--ink);padding-top:12px}}
.step b{{display:block;font-size:14px;margin-bottom:4px}}
.step span{{color:var(--ink2);font-size:14px}}
.decision{{display:flex;gap:16px;align-items:flex-start;background:var(--ink);color:#fff;border-radius:16px;
padding:20px 24px;margin:18px 0 8px}}
.decision .mono{{color:var(--yellow);white-space:nowrap;padding-top:3px}}
.decision p{{margin:0;font-size:16px;color:#E6E4F0}}
table.m{{width:100%;border-collapse:separate;border-spacing:0 6px;font-size:14px}}
table.m th{{text-align:left;color:var(--muted);font-weight:500;font-size:12px;padding:0 8px}}
table.m td{{padding:9px 8px;white-space:nowrap;background:#FBF9F5;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}}
table.m td:first-child{{border-left:1px solid var(--line);border-radius:10px 0 0 10px;font-weight:500}}
table.m td:last-child{{border-right:1px solid var(--line);border-radius:0 10px 10px 0;color:var(--ink2)}}
.pill{{display:inline-block;white-space:nowrap;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600}}
.p-ok{{background:#E3F1EA;color:var(--good)}}.p-no{{background:#F9E3DF;color:var(--bad)}}.p-chk{{background:#FBEFD7;color:var(--warn)}}
.unv{{color:var(--muted);font-weight:400}}
.console{{background:#0F0E26;color:#D9D7EA;border-radius:14px;padding:18px 20px;font:13px/1.7 'JB Mono',monospace}}
.console .pr{{color:var(--yellow)}}.console .blk{{color:#FF8A75;font-weight:700}}.console .dim{{color:#8C89A8}}
.banner{{display:flex;justify-content:space-between;align-items:center;border-radius:12px;padding:12px 18px;
font-size:14px;font-weight:600;margin-bottom:18px}}
.banner.draft{{background:#FFF4D1;color:#7A5300;border:1px solid #F2D27A}}
.banner.ok{{background:#E3F1EA;color:var(--good);border:1px solid #B9DCCB}}
.banner .hash{{font:500 12px 'JB Mono',monospace;opacity:.75}}
ul.notes{{margin:0;padding:0;list-style:none}}
ul.notes li{{padding:12px 0;border-bottom:1px solid var(--line);font-size:15px}}
ul.notes li:last-child{{border-bottom:0}}
ul.notes li b{{display:inline-block;min-width:118px;color:var(--gold);font:500 12px 'JB Mono',monospace;
text-transform:uppercase;letter-spacing:.06em}}
.foot{{color:var(--muted);font-size:12.5px;margin-top:10px}}
footer{{padding:48px 0 64px;color:var(--muted);font-size:13px}}
@media print{{nav.toc{{display:none}}section.proj{{page-break-before:always}}}}
""")


def esc(x):
    return html.escape(str(x))


# ---------------- charts (inline SVG, direct labels, no legends) ----------------
def _svg(w, h, body, label):
    return (f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{esc(label)}" '
            f'style="font-family:Inter,sans-serif;display:block">{body}</svg>')


def columns(values, labels, target, highlight=None, fmt=lambda v: f"{v}", note=None, label="Columns"):
    W, H, top, bot, left = 520, 250, 36, 30, 6
    mx = max(max(values), target) * 1.15
    n = len(values)
    bw = (W - left * 2) / n * 0.62
    gap = (W - left * 2) / n
    y = lambda v: top + (H - top - bot) * (1 - v / mx)
    out = []
    for i, v in enumerate(values):
        x = left + i * gap + (gap - bw) / 2
        hi = i == highlight
        miss = v < target
        col = BAD if (hi and miss) else (INK if hi else ("#B9B2A3" if miss else "#8F88A6"))
        out.append(f'<rect x="{x:.1f}" y="{y(v):.1f}" width="{bw:.1f}" height="{H-bot-y(v):.1f}" rx="4" fill="{col}"/>')
        out.append(f'<text x="{x+bw/2:.1f}" y="{H-10}" font-size="14" fill="{MUTED}" text-anchor="middle">{esc(labels[i])}</text>')
        if hi:
            out.append(f'<text x="{x+bw/2:.1f}" y="{y(v)-8:.1f}" font-size="16" font-weight="700" fill="{col}" text-anchor="middle">{esc(fmt(v))}</text>')
    ty = y(target)
    out.append(f'<line x1="{left}" x2="{W-left}" y1="{ty:.1f}" y2="{ty:.1f}" stroke="{GOLD}" stroke-width="1.5" stroke-dasharray="5 4"/>')
    out.append(f'<rect x="{left}" y="{ty-24:.1f}" width="118" height="20" rx="4" fill="#fff"/>'
               f'<text x="{left+4}" y="{ty-9:.1f}" font-size="14" font-weight="600" fill="{GOLD}">Target {esc(fmt(target))}</text>')
    if False:
        x = left + highlight * gap + gap / 2
        out.append(f'<text x="{x-bw/2-8:.1f}" y="{top+2}" font-size="14" fill="{INK2}" text-anchor="end">{esc(note)}</text>')
    return _svg(W, H, "".join(out), label)


def interval(point, lo, hi, target, axis=(-1, 6), unit=" pts", label="Interval"):
    W, H, l, r = 420, 160, 18, 18
    a0, a1 = axis
    x = lambda v: l + (W - l - r) * (v - a0) / (a1 - a0)
    o = [f'<line x1="{l}" x2="{W-r}" y1="92" y2="92" stroke="{LINE}" stroke-width="2"/>']
    for t in range(int(a0), int(a1) + 1):
        o.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="88" y2="96" stroke="{NEUTRAL}"/>'
                 f'<text x="{x(t):.1f}" y="116" font-size="13" fill="{MUTED}" text-anchor="middle">{t:+d}</text>')
    o.append(f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="40" y2="100" stroke="{MUTED}" stroke-width="1"/>'
             f'<text x="{x(0):.1f}" y="34" font-size="13" fill="{MUTED}" text-anchor="middle">No effect</text>')
    o.append(f'<line x1="{x(target):.1f}" x2="{x(target):.1f}" y1="56" y2="100" stroke="{GOLD}" stroke-dasharray="4 3"/>'
             f'<text x="{x(target):.1f}" y="50" font-size="13" font-weight="600" fill="{GOLD}" text-anchor="middle">Target</text>')
    o.append(f'<rect x="{x(lo):.1f}" y="82" width="{x(hi)-x(lo):.1f}" height="20" rx="10" fill="rgba(23,21,58,.14)"/>')
    o.append(f'<circle cx="{x(point):.1f}" cy="92" r="8" fill="{INK}"/>')
    o.append(f'<text x="{x(point):.1f}" y="148" font-size="15" font-weight="700" fill="{INK}" text-anchor="middle">'
             f'{point:+.1f}{unit}, range {lo:+.1f} to {hi:+.1f}</text>')
    return _svg(W, H, "".join(o), label)


def hbars(rows, fmt, label="Bars"):
    """rows: (label, value, kind, (lo, hi) or None); kind in {'ink','ghost'}"""
    W, rowh, l = 520, 76, 150
    mx = max(r[1] if not r[3] else max(r[1], r[3][1]) for r in rows) * 1.32
    H = rowh * len(rows) + 10
    x = lambda v: l + (W - l - 20) * v / mx
    o = []
    for i, (lab, v, kind, rng) in enumerate(rows):
        y0 = 10 + i * rowh
        o.append(f'<text x="0" y="{y0+27}" font-size="15" font-weight="600" fill="{INK}">{esc(lab)}</text>')
        if kind == "ghost":
            o.append(f'<rect x="{l}" y="{y0+8}" width="{x(v)-l:.1f}" height="30" rx="6" fill="#ECE6DA" '
                     f'stroke="{NEUTRAL}" stroke-dasharray="4 3"/>')
        else:
            o.append(f'<rect x="{l}" y="{y0+8}" width="{x(v)-l:.1f}" height="30" rx="6" fill="{INK}"/>')
        if rng:
            o.append(f'<line x1="{x(rng[0]):.1f}" x2="{x(rng[1]):.1f}" y1="{y0+52}" y2="{y0+52}" stroke="{GOLD}" stroke-width="4" stroke-linecap="round"/>'
                     f'<text x="{l}" y="{y0+70}" font-size="13" fill="{GOLD}">range {esc(fmt(rng[0]))} to {esc(fmt(rng[1]))}</text>')
        o.append(f'<text x="{x(v)+8:.1f}" y="{y0+29}" font-size="17" font-weight="700" fill="{INK if kind!="ghost" else MUTED}">{esc(fmt(v))}</text>')
    return _svg(W, H, "".join(o), label)


def waterfall(start_label, start, steps, end_label, fmt, label="Bridge"):
    W, H, top, bot = 420, 270, 30, 40
    vals = [start]
    run = start
    for _, d in steps:
        run += d
        vals.append(run)
    lo = min(vals + [run]) * 0.88
    hi = max(vals + [start]) * 1.05
    n = len(steps) + 2
    gap = W / n
    bw = gap * 0.7
    y = lambda v: top + (H - top - bot) * (1 - (v - lo) / (hi - lo))
    o = []
    def bar(i, a, b, col, txt):
        x0 = i * gap + (gap - bw) / 2
        y1, y2 = sorted((y(a), y(b)))
        o.append(f'<rect x="{x0:.1f}" y="{y1:.1f}" width="{bw:.1f}" height="{max(y2-y1,2):.1f}" rx="3" fill="{col}"/>')
        o.append(f'<text x="{x0+bw/2:.1f}" y="{y1-7:.1f}" font-size="14" font-weight="700" fill="{col}" text-anchor="middle">{esc(txt)}</text>')
        return x0
    bar(0, lo, start, "#8F88A6", fmt(start, False))
    run = start
    for i, (lab, d) in enumerate(steps, start=1):
        bar(i, run, run + d, GOOD if d >= 0 else BAD, fmt(d, True))
        run += d
    bar(n - 1, lo, run, INK, fmt(run, False))
    labs = [start_label] + [s[0] for s in steps] + [end_label]
    for i, t in enumerate(labs):
        o.append(f'<text x="{i*gap+gap/2:.1f}" y="{H-14}" font-size="13" fill="{INK2}" text-anchor="middle">{esc(t)}</text>')
    return _svg(W, H, "".join(o), label)


def page(title, body):
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{esc(title)}</title>"
            f"<style>{css()}</style></head><body>{body}</body></html>")
