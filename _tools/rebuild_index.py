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

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(_HERE)
CAT = json.load(open(os.path.join(_HERE, "catalog2.json"), encoding="utf-8"))
S = CAT["strategies"]
WHOP_STORE = CAT.get("whop_store") or "/"

def esc(s):
    return html.escape(str(s), quote=False)

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
        f'<td class="sx-n"><a href="/strategies/{p["slug"]}.html">{name}</a>'
        f'<span class="sx-sub">{sub}</span>{note}</td>'
        f'<td class="sx-s">{esc(session_of(p))}</td>'
        f'<td class="sx-f">{esc(b.get("Win", "—"))}</td>'
        f'<td class="sx-f">{esc(b.get("PF", "—"))}</td>'
        f'<td class="sx-f">{esc(b.get("RoDD", "—"))}</td>'
        f'<td class="sx-f">{esc(b.get("Net", "—"))}</td>'
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
      <th scope="col" class="sx-s">Session</th>
      <th scope="col" class="sx-f">Win</th>
      <th scope="col" class="sx-f">PF</th>
      <th scope="col" class="sx-f">RoDD</th>
      <th scope="col" class="sx-f">Net</th>
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

DISCLAIM_SHORT = ("All performance figures are backtested or validation-run results at the position size each "
    "strategy&rsquo;s validated run used, shown with commissions and slippage modeled. Backtested performance is "
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

<header class="sx-head">
  <p class="sx-mark">Futures<strong>TradingBots</strong></p>
  <p class="sx-eff">Strategy specification sheet · effective {esc(today)} · supersedes all prior sheets
  <!-- WHOP: storefront link --> · <a href="{esc(WHOP_STORE)}" rel="noopener">Get access</a></p>
</header>

<main class="sx-main">
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

  <div class="sx-legal">
    <p>{DISCLAIM_SHORT}</p>
    <p>{DISCLAIM_LONG}</p>
  </div>
</main>

<footer class="sx-foot">
  <p><a href="/terms.html">Terms</a> · <a href="/privacy.html">Privacy</a> · <a href="/plan.html">Plan finder</a>
  · <!-- DISCORD: community invite --><a href="https://discord.gg/BBXDDn9pCD" rel="noopener">Discord</a>
  · <!-- WHOP: storefront --><a href="{esc(WHOP_STORE)}" rel="noopener">Whop</a></p>
  <p class="sx-fine">FuturesTradingBots · support via Discord or the chat on your Whop purchase page.</p>
</footer>

</body>
</html>
"""

out = os.path.join(BASE, "index.html")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    f.write(page)
print(f"index written: spec sheet, {len(mnq)} MNQ rows + {len(mgc)} MGC rows, effective {today}")
