"""Generate index.html — the specification sheet (rebrand r4, seed 77810f1d).

The catalog page is an exchange-style contract specification document: white
paper, hairline rules, one exchange blue, tabular-mono figures. Two ranked
tables (MNQ/NQ, then MGC), books ranked inline and labeled as combinations.
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
        f'<td class="sx-f sx-rodd">{pct(b.get("RoDD", 0)) if b.get("RoDD") else "—"}</td>'
        f'<td class="sx-f">{esc(b.get("Win", "—"))}</td>'
        f'<td class="sx-f">{esc(b.get("PF", "—"))}</td>'
        f'<td class="sx-f">{esc(b.get("Net", "—"))}</td>'
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
    <caption class="sr-only">{esc(title)}: {n} strategies ranked by best-window return on maximum drawdown</caption>
    <thead><tr>
      <th scope="col" class="sx-r" aria-label="Rank">#</th>
      <th scope="col" class="sx-n">Strategy</th>
      <th scope="col" class="sx-f sx-rodd">RoDD</th>
      <th scope="col" class="sx-f">Win</th>
      <th scope="col" class="sx-f">PF</th>
      <th scope="col" class="sx-f">Net</th>
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
<meta name="description" content="Futures strategies for MNQ/NQ and MGC, delivered as TradingView invite-only scripts. Best validated window and full record published for every strategy.">
<link rel="canonical" href="https://futurestradingbots.com/">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&amp;family=Fragment+Mono&amp;display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/main.css?v=00000000">
</head>
<body class="sx-doc">
<a class="skip" href="#main">Skip to content</a>

<header>
  <div class="wrap nav">
    <a class="brand" href="/"><svg class="bmark" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path class="bmark-ant" d="M12 3.6V7.2"/><circle class="bmark-node" cx="12" cy="2.4" r="1.5"/><rect class="bmark-head" x="3.6" y="7.2" width="16.8" height="13" rx="3.4"/><rect class="bmark-eye" x="8" y="10.3" width="2.3" height="6.4" rx="1.15"/><rect class="bmark-eye" x="13.7" y="11.9" width="2.3" height="4.6" rx="1.15"/></svg><span class="bname">FUTURES<small>TRADING<span class="mk">BOTS</span></small></span></a>
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
  <p class="sx-lede">{len(S)} futures strategies for MNQ/NQ and MGC, sold as TradingView invite-only scripts
  and activated to your TradingView username within 24 hours.</p>
  <p class="sx-note">Figures below are each strategy&rsquo;s best validated window, commissions and slippage modeled.
  The full record, good or ugly, is published on every specification page. Ranked by return on maximum
  drawdown (RoDD). Net is the window&rsquo;s closed-trade total at the validated run&rsquo;s position size.</p>

{table("MNQ / NQ · Nasdaq futures", mnq_rows, len(mnq))}

{table("MGC · Gold futures", mgc_rows, len(mgc))}

  <p class="sx-all"><!-- WHOP: replace with All-Access checkout link when it exists -->
  All {len(S)} strategies under one subscription: <a href="/strategies/all-access.html">All-Access — ${CAT["bundles"]["all_access"]["price"]} / mo</a>.
  Not sure where to start: <a href="/plan.html">the plan finder</a> ranks them against your drawdown budget.</p>

</main>

<footer>
  <div class="wrap">
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
