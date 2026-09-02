"""Generate index.html — the specification sheet (rebrand r4, seed 77810f1d).

The catalog page is an exchange-style contract specification document: white
paper, hairline rules, one exchange blue, tabular-mono figures. Two ranked
tables (MNQ, then MGC), books ranked inline and labeled as combinations.
The whole file is generated from catalog2.json — no hand-edited regions.
The previous quant-terminal index and its generator are archived at
_tools/archive/*quantterminal-20260901* and git tag pre-rebrand-20260901.
Order of builds is unchanged: gen_pages -> rebuild_index -> gen_plan ->
recompute the main.css hash -> restamp ?v= on every page. This generator no
longer writes any CSS region; the spec-sheet styles are a static block at the
end of assets/main.css.
"""
import json, os, html, datetime
from glyphs import glyph

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(_HERE)
CAT = json.load(open(os.path.join(_HERE, "catalog2.json"), encoding="utf-8"))
S = CAT["strategies"]
WHOP_STORE = CAT.get("whop_store") or "/"
PROMO = CAT.get("promo") or {}
PROMO_LINE = PROMO.get("line", "").replace("{code}", PROMO.get("code", "")) if PROMO else ""

def esc(s):
    return html.escape(str(s), quote=False)

def num(v):
    s = str(v).replace("$", "").replace(",", "").replace("%", "")
    m = 1000 if s.endswith("k") else 1
    try: return float(s.rstrip("k")) * m
    except ValueError: return 0.0

def pct(v):
    """RoDD-style ratios sell as percentages: 11.06x -> 1,106%."""
    return "{:,.0f}%".format(num(v) * 100)

def rodd_mo_pct(stats):
    """Average monthly return on drawdown, as a percentage, computed fresh
    from RoDD / Months (owner ruling 2026-09-02)."""
    rodd, months = num(stats.get("RoDD", 0)), num(stats.get("Months", 0))
    return "{:,.0f}%".format(rodd / months * 100) if months else "—"

def bs(p, k):
    return p["best"]["stats"].get(k, "—")

def avg_monthly_profit(p):
    """Average monthly net profit over the best window, at the shown multiplier — from the real
    trade record when it is on disk (exact net / months), else from the catalog display strings."""
    tr = load_trades(p["slug"])
    if tr and tr.get("best", {}).get("months"):
        return tr["best"]["net"] / tr["best"]["months"]
    months = num(bs(p, "Months"))
    return num(bs(p, "Net")) / months if months else 0.0

def money_signed(v):
    sign = "+" if v >= 0 else "&minus;"
    return "{}${:,.0f}".format(sign, abs(v))

def profit_cell(p):
    v = avg_monthly_profit(p)
    cls = "sx-pos" if v >= 0 else "sx-neg"
    return f'<span class="{cls}">{money_signed(v)}</span><small class="sx-mo">per month</small>'

# ── flagship cover-flow (5 slots — the CSS ring is built for exactly five) ──
def load_trades(slug):
    p = os.path.join(_HERE, "trades", slug + ".json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))

SPARK_W, SPARK_H = 1200.0, 300.0

def sparkline(slug, cls="fspark", pfx="fsg", maxpts=0):
    """Full-bleed equity curve for a flagship pane, from the real record."""
    tr = load_trades(slug)
    pts = (tr or {}).get("equity") or []
    if len(pts) < 2:
        return ""
    if maxpts and len(pts) > maxpts:
        step = len(pts) / float(maxpts)
        idx = sorted({int(i * step) for i in range(maxpts)} | {len(pts) - 1})
        pts = [pts[i] for i in idx]
    ys = [v for _, v in pts]
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or 1.0
    n = len(pts)
    PAD = 6.0
    def X(i): return PAD + (SPARK_W - 2 * PAD) * i / (n - 1)
    def Y(v): return PAD + (SPARK_H - 2 * PAD) * (1.0 - (v - lo) / span)
    line = " ".join(f"{X(i):.1f} {Y(v):.1f}" for i, (_, v) in enumerate(pts))
    return (
        f'<svg class="{cls}" viewBox="0 0 {SPARK_W:.0f} {SPARK_H:.0f}" preserveAspectRatio="none" '
        f'aria-hidden="true" focusable="false">'
        f'<defs><linearGradient id="{pfx}-{slug}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop class="{pfx}-a" offset="0"/><stop class="{pfx}-b" offset="1"/></linearGradient></defs>'
        f'<path class="{cls}-area" fill="url(#{pfx}-{slug})" d="M{PAD:.1f} {SPARK_H:.1f} L{line} '
        f'L{SPARK_W - PAD:.1f} {SPARK_H:.1f} Z"/>'
        f'<path class="{cls}-line" fill="none" d="M{line}"/></svg>')

BASE_DD = CAT.get("baseline_dd", 5000)

def baseline(p):
    return num(bs(p, "RoDD")) * BASE_DD

TOP5 = sorted(S, key=lambda x: (-x["price"], -num(bs(x, "RoDD"))))[:5]
RODD_RANK = {p["slug"]: i + 1 for i, p in enumerate(sorted(S, key=lambda x: -num(bs(x, "RoDD"))))}

def cf_block():
    radios = '<input class="cf-r" type="radio" name="cf-sel" id="cf-0" checked>' + "".join(
        f'<input class="cf-r" type="radio" name="cf-sel" id="cf-{i+1}">' for i in range(len(TOP5)))
    panes = ""
    for i, p in enumerate(TOP5):
        rk = RODD_RANK[p["slug"]]
        tag = f"#{rk} RoDD" if rk <= 3 else "RoDD"
        panes += (
            f'<div class="cf-pane fc-{p["slug"]}">'
            f'<a class="cf-link" href="/strategies/{p["slug"]}.html">'
            + sparkline(p["slug"], cls="cf-spark", pfx="cf-sg", maxpts=64)
            + f'<span class="cf-glyphwrap" aria-hidden="true">{glyph(p["slug"], "glyph cf-glyph")}</span>'
            + f'<span class="cf-star"><i>{tag}</i></span>'
            + f'<span class="cf-mid"><b class="cf-mid-profit">{money_signed(avg_monthly_profit(p))}<small>/mo</small></b>'
            + f'<span class="cf-mid-lab">avg monthly profit</span>'
            + f'<b class="cf-mid-win">{esc(bs(p, "Win"))}</b><span class="cf-mid-lab">win rate</span></span>'
            + f'<span class="cf-foot"><span class="cf-titlerow"><b class="cf-name">{esc(p["name"])}</b>'
            + f'<span class="cf-price">${p["price"]}<small>/mo</small></span></span>'
            + f'<span class="cf-gain">{rodd_mo_pct(p["best"]["stats"])}</span>'
            + f'<span class="cf-win">avg monthly return on drawdown &middot; best window</span></span></a>'
            f'<label class="cf-pick" for="cf-{i+1}"><span class="sr-only">Bring {esc(p["name"])} to the front</span></label>'
            f'</div>')
    dots = "".join(
        f'<label class="cf-dot fc-{p["slug"]}" for="cf-{i+1}"><span class="sr-only">{esc(p["name"])}</span></label>'
        for i, p in enumerate(TOP5))
    return (radios + f'<div class="cf-stage">{panes}</div>'
            f'<div class="cf-dots">{dots}'
            '<label class="cf-play" for="cf-0"><span class="cf-play-ico" aria-hidden="true"></span>'
            '<span class="sr-only">Resume the automatic rotation</span></label></div>')

def buy_href(p):
    return p.get("whop") or f"/strategies/{p['slug']}.html"

def market_of(p):
    first = p["meta"].split("·")[0].strip().upper()
    return "MGC" if "MGC" in first else "MNQ"

# Session-vocabulary overrides where the meta's second token is not a session
# term (a spec sheet keeps one vocabulary; the meta itself feeds the pinned
# product pages and stays untouched).
SESSION_OVERRIDE = {"slipstream": "all sessions"}

def session_of(p):
    # meta shape: "MNQ · 08:30 ET — the range fade, five days a week"
    # (one legacy entry uses " - " instead of the em dash)
    if p["slug"] in SESSION_OVERRIDE:
        return SESSION_OVERRIDE[p["slug"]]
    try:
        part = p["meta"].split("·", 1)[1]
        part = part.split("—")[0].split(" - ")[0]
        return part.strip()
    except IndexError:
        return ""

def row(p, rank):
    b = p["best"]["stats"]
    name = esc(p["name"])
    sub = esc(p["actual"])
    note = ""
    if p.get("legs"):
        note = f'<span class="sx-book">book · combines {len(p["legs"])} strategies</span>'
    return (
        f'<tr>'
        f'<td class="sx-r">{rank}</td>'
        f'<td class="sx-n"><a class="fc-{p["slug"]}" href="/strategies/{p["slug"]}.html">{glyph(p["slug"], "glyph sx-g")}{name}</a>'
        f'<span class="sx-sub">{sub}</span>{note}</td>'
        f'<td class="sx-f sx-rodd">{rodd_mo_pct(b) if b.get("RoDD") else "—"}</td>'
        f'<td class="sx-f">{esc(b.get("Win", "—"))}</td>'
        f'<td class="sx-f">{esc(b.get("PF", "—"))}</td>'
        f'<td class="sx-f sx-net">{profit_cell(p)}</td>'
        f'<td class="sx-f">{("&times;" + str(p["mult"])) if p.get("mult") else "—"}</td>'
        f'<td class="sx-s">{esc(session_of(p))}</td>'
        f'<td class="sx-f sx-p"><!-- WHOP: replace this product-page link with the Whop checkout link -->'
        f'<a href="{esc(buy_href(p))}" rel="noopener">${p["price"]}</a></td>'
        f'</tr>'
    )

def table(title, rows_html, n):
    return f"""<section class="sx-sec">
  <h2>{esc(title)}</h2>
  <div class="sx-scroll" tabindex="0" role="region" aria-label="{esc(title)} specification table, scrolls horizontally on small screens">
  <table class="sx-t">
    <caption class="sr-only">{esc(title)}: {n} strategies ranked by average monthly return on drawdown</caption>
    <thead><tr>
      <th scope="col" class="sx-r" aria-label="Rank">#</th>
      <th scope="col" class="sx-n">Strategy</th>
      <th scope="col" class="sx-f sx-rodd"><abbr title="Average monthly return on drawdown">RoDD/mo</abbr></th>
      <th scope="col" class="sx-f">Win Rate</th>
      <th scope="col" class="sx-f">Profit Factor</th>
      <th scope="col" class="sx-f sx-net"><abbr title="Average monthly net profit over the best window, at the shown multiplier">Avg Monthly Profit</abbr></th>
      <th scope="col" class="sx-f"><abbr title="Multiplier the published figures are shown at">Mult</abbr></th>
      <th scope="col" class="sx-s">Session</th>
      <th scope="col" class="sx-f sx-p">$ / mo</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  </div>
</section>"""

mnq = [p for p in S if market_of(p) == "MNQ"]
mgc = [p for p in S if market_of(p) == "MGC"]
mnq_rows = "".join(row(p, i) for i, p in enumerate(mnq, 1))
mgc_rows = "".join(row(p, i) for i, p in enumerate(mgc, 1))
today = datetime.date.today().strftime("%#d %b %Y") if os.name == "nt" else datetime.date.today().strftime("%-d %b %Y")

DISCLAIM_SHORT = ("All performance figures are backtested or validation-run results shown with commissions and "
    "slippage modeled, on the stated window. Backtested performance is "
    "hypothetical, does not represent live trading results, and is not a guarantee or projection of future returns. "
    "Futures trading involves substantial risk of loss and is not suitable for all investors. Nothing on this site "
    "is financial advice. Access provides the strategy tool only; you are responsible for your own trading decisions.")

DISCLAIM_LONG = ("<strong>Risk disclosure.</strong> Futures and derivatives trading involves substantial risk of loss "
    "and is not suitable for every investor. You may lose more than your initial investment. Only risk capital should "
    "be used for trading, and only those with sufficient risk capital should consider trading. "
    "<strong>Hypothetical performance disclaimer.</strong> Performance figures displayed on this site are hypothetical "
    "or simulated. Hypothetical performance results have many inherent limitations. No representation is being made "
    "that any account will or is likely to achieve profits or losses similar to those shown; in fact, there are "
    "frequently sharp differences between hypothetical performance results and the actual results subsequently "
    "achieved by any particular trading program. One of the limitations of hypothetical performance results is that "
    "they are generally prepared with the benefit of hindsight. FuturesTradingBots is a software publisher. Nothing "
    "on this site constitutes financial, investment, legal, or tax advice, or a solicitation to buy or sell any "
    "financial instrument. Purchases, billing, and subscription management are processed by Whop; TradingView is a "
    "trademark of TradingView, Inc.")

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; base-uri 'none'; form-action 'none'; upgrade-insecure-requests">
<title>FuturesTradingBots — MNQ &amp; MGC futures strategies</title>
<meta name="description" content="Futures strategies for MNQ and MGC, delivered as TradingView invite-only scripts. Best validated window and full record published for every strategy.">
<link rel="canonical" href="https://futurestradingbots.com/">
<meta name="theme-color" content="#131722">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&amp;family=Fragment+Mono&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/main.css?v=00000000">
</head>
<body class="sx-doc">
<a class="skip" href="#main">Skip to content</a>

<header>
  <div class="wrap nav">
    <a class="brand" href="/"><img class="brand-logo" src="/assets/aft-logo.png" alt="All Fluence Trading" width="985" height="260"></a>
    <nav class="nav-links" aria-label="Main">
      <a href="/">All strategies</a>
      <a href="/strategies/all-access.html">All-Access</a>
      <a class="nav-plan" href="/plan.html">Plan finder</a>
    </nav>
    <!-- WHOP: storefront -->
    <a class="btn btn-sm btn-buy" href="{esc(WHOP_STORE)}" rel="noopener">Get access</a>
    <!-- DISCORD: community invite -->
    <a class="btn btn-sm btn-discord" href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener"><svg class="ic-discord" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.7 17.4c-3.2-.1-4.9-1.7-4.9-1.7.3-4 1.4-6.6 2.7-8.3C7.8 6.4 9.2 6 9.2 6l.5 1.1c1.5-.3 3.1-.3 4.6 0L14.8 6s1.4.4 2.7 1.4c1.3 1.7 2.4 4.3 2.7 8.3 0 0-1.7 1.6-4.9 1.7l-.8-1.1c-1.6.3-3.4.3-5 0z"/><circle cx="9.6" cy="12.6" r="1.15" fill="currentColor" stroke="none"/><circle cx="14.4" cy="12.6" r="1.15" fill="currentColor" stroke="none"/></svg><span>Discord</span></a>
    <details class="nav-mob">
      <summary aria-label="Menu"><span class="burger" aria-hidden="true"><i></i><i></i><i></i></span></summary>
      <nav class="nav-mob-panel" aria-label="Mobile">
        <a href="/">All strategies</a>
        <a href="/strategies/all-access.html">All-Access</a>
        <a href="/plan.html">Plan finder</a>
        <!-- DISCORD: community invite -->
        <a href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener">Discord</a>
      </nav>
    </details>
  </div>
</header>

<main class="sx-main" id="main">
  <div class="sx-hero">
    <div class="sx-hero-copy">
      <h1 class="sx-hero-h1">Strategies engineered to be <span class="hl">measured</span>, not believed.</h1>
      <p class="sx-lede">{len(S)} futures strategies for MNQ and MGC, sold as TradingView invite-only scripts
      and activated to your TradingView username within 24 hours.</p>
      <p class="sx-cta">Select any of the profitable strategies below to see the trade details and results.</p>
      <p class="sx-note">Figures below are each strategy&rsquo;s best validated window, commissions and slippage modeled.
      The full record, good or ugly, is published on every specification page. Ranked by average monthly return
      on drawdown (RoDD/mo) &mdash; return on drawdown = net profit &divide; maximum drawdown over the window,
      shown per month of the record. Avg Monthly Profit = the window&rsquo;s closed-trade net profit divided by
      its months, at the shown multiplier. Win Rate and Profit Factor are the window&rsquo;s closed-trade figures.</p>
      <p class="sx-promo">{esc(PROMO_LINE)}</p>
    </div>
    <div class="coverflow" aria-label="Flagship strategies">{cf_block()}</div>
  </div>

  <p class="sx-ddnote">All strategies simulated based on a $10,000 or less drawdown.</p>

{table("MNQ · Nasdaq futures", mnq_rows, len(mnq))}

{table("MGC · Gold futures", mgc_rows, len(mgc))}

  <p class="sx-all"><!-- WHOP: replace with All-Access checkout link when it exists -->
  All {len(S)} strategies under one subscription: <a href="/strategies/all-access.html">All-Access — ${CAT["bundles"]["all_access"]["price"]} / mo</a>.
  Not sure where to start: <a href="/plan.html">the plan finder</a> ranks them against your drawdown budget.</p>

  <p class="sx-promo">{esc(PROMO_LINE)}</p>

</main>

<footer>
  <div class="wrap">
<img class="foot-logo" src="/assets/aft-logo.png" alt="All Fluence Trading" width="985" height="260">
<div class="foot-links">
      <a href="/">All strategies</a>
      <a href="/strategies/all-access.html">All-Access</a>
      <a href="/plan.html">Plan finder</a>
      <a href="/terms.html">Terms</a>
      <a href="/privacy.html">Privacy</a>

      <!-- DISCORD: community invite -->
      <a class="foot-discord" href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener"><svg class="ic-discord" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.7 17.4c-3.2-.1-4.9-1.7-4.9-1.7.3-4 1.4-6.6 2.7-8.3C7.8 6.4 9.2 6 9.2 6l.5 1.1c1.5-.3 3.1-.3 4.6 0L14.8 6s1.4.4 2.7 1.4c1.3 1.7 2.4 4.3 2.7 8.3 0 0-1.7 1.6-4.9 1.7l-.8-1.1c-1.6.3-3.4.3-5 0z"/><circle cx="9.6" cy="12.6" r="1.15" fill="currentColor" stroke="none"/><circle cx="14.4" cy="12.6" r="1.15" fill="currentColor" stroke="none"/></svg><span>Discord</span></a>
    </div>
    <p class="disclaimer">{DISCLAIM_SHORT}</p>
    <p class="disclaimer">
      {DISCLAIM_LONG}
    </p>
    <div class="copyright">© 2026 FuturesTradingBots · futurestradingbots.com</div>
  </div>
</footer>

</body>
</html>
"""

out = os.path.join(BASE, "index.html")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(page)
print(f"index written: spec sheet, {len(mnq)} MNQ rows + {len(mgc)} MGC rows, effective {today}")
