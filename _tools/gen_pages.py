"""Generate product pages, bundle pages, success, 404, and sitemap from catalog2.json.
catalog2.json is curated from the owners' validation playbook — every figure on every
page traces to it. Never hand-edit generated pages; edit the catalog or this template."""
import json, html, os, sys, hashlib
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import charts

BASE = os.path.dirname(_HERE)  # repo root
CAT = json.load(open(os.path.join(_HERE, "catalog2.json"), encoding="utf-8"))
SITE = "https://goal33systems.com"
TODAY = "2026-08-20"
CSSV = hashlib.md5(open(os.path.join(BASE, "assets", "main.css"), "rb").read()).hexdigest()[:8]

DISCLAIMER = ("All performance figures are backtested or validation-run results shown with commissions and "
              "slippage modeled, on the stated window. Backtested performance is hypothetical, does not "
              "represent live trading results, and is not a guarantee or projection of future returns. Futures "
              "trading involves substantial risk of loss and is not suitable for all investors. Nothing on this "
              "site is financial advice. Access provides the strategy tool only; you are responsible for your "
              "own trading decisions.")

NOTCHES = [1000, 2500, 5000, 10000, 25000, 50000]

def esc(s): return html.escape(str(s), quote=False)

def num(v):
    s = str(v).replace("$", "").replace(",", "").replace("%", "")
    m = 1000 if s.endswith("k") else 1
    try: return float(s.rstrip("k")) * m
    except ValueError: return 0.0

def usd(v):
    return "${:,.0f}".format(v)

def is_hot(key, val):
    v = num(val)
    return {"RoDD": v >= 10, "PF": v >= 2.0, "Win": v >= 80, "Trades": v >= 1000,
            "Net": v >= 150000}.get(key, False)

# ── shared page skeleton ────────────────────────────────────────
def head(title, desc, path):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; base-uri 'none'; form-action 'none'; upgrade-insecure-requests">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{esc(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="theme-color" content="#051014">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:site_name" content="Goal33 Systems">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}{path}">
<link rel="canonical" href="{SITE}{path}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/main.css?v={CSSV}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>

<header>
  <div class="wrap nav">
    <a class="brand" href="/">GOAL<span class="n33">33</span><small>SYSTEMS</small></a>
    <nav class="nav-links" aria-label="Main">
      <a href="/#strategies">Strategies</a>
      <a href="/#packages">Bundles</a>
      <a href="/#how">How access works</a>
      <a href="/#faq">FAQ</a>
    </nav>
    <!-- WHOP: replace this link with the Whop storefront URL -->
    <a class="btn btn-sm btn-solid" href="/#packages" rel="noopener">Get access</a>
  </div>
</header>

<main id="main">
"""

FOOTER = f"""</main>

<footer>
  <div class="wrap">
    <div class="foot-links">
      <a href="/#strategies">Strategies</a>
      <a href="/#packages">Bundles</a>
      <a href="/#how">How access works</a>
      <!--email_off--><a href="mailto:support@goal33systems.com">support@goal33systems.com</a><!--/email_off-->
    </div>
    <p class="disclaimer">{esc(DISCLAIMER)}</p>
    <p class="disclaimer">
      <strong>Risk disclosure.</strong> Futures and derivatives trading involves substantial risk of loss
      and is not suitable for every investor. You may lose more than your initial investment. Only risk
      capital should be used for trading, and only those with sufficient risk capital should consider trading.
      <strong>Hypothetical performance disclaimer.</strong> Performance figures displayed on this site are
      hypothetical or simulated. Hypothetical performance results have many inherent limitations. No
      representation is being made that any account will or is likely to achieve profits or losses similar
      to those shown; in fact, there are frequently sharp differences between hypothetical performance
      results and the actual results subsequently achieved by any particular trading program. One of the
      limitations of hypothetical performance results is that they are generally prepared with the benefit
      of hindsight. Goal33 Systems is a software publisher. Nothing on this site constitutes financial,
      investment, legal, or tax advice, or a solicitation to buy or sell any financial instrument. Purchases,
      billing, and subscription management are processed by Whop; TradingView is a trademark of TradingView, Inc.
    </p>
    <div class="copyright">© 2026 GOAL33 SYSTEMS · GOAL33SYSTEMS.COM</div>
  </div>
</footer>

</body>
</html>
"""

def buybox(name, price, whop_note, xsell=None, struck=None):
    was = f'<s class="was">${struck}<span class="sr-only"> combined value,</span></s>' if struck else ""
    xs = xsell or ('Bundles: <a href="/strategies/all-access.html">All-Access — $999/mo</a> · '
                   '<a href="/strategies/pick-3.html">Pick-3 — $499/mo</a>')
    return f"""<aside class="buybox" aria-label="Purchase {html.escape(name)}">
  <div class="price">{was}<span class="now">${price}</span><span class="per">/MO</span></div>
  <span class="annual">Annual = 2 months free</span>
  <!-- WHOP: paste checkout link ({whop_note}) -->
  <a class="btn btn-buy" href="#" rel="noopener">Get access</a>
  <ul>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>TradingView invite-only script, activated within 24h</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Alert templates and setup documentation</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Automate it through TradingView alerts and your own execution tooling, or run it as an aid to manual trading</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Cancel anytime through Whop; access revokes automatically</span></li>
  </ul>
  <p class="xsell">{xs}</p>
</aside>"""

# ── components ──────────────────────────────────────────────────
ORDER = ["RoDD", "RoDD/mo", "PF", "Win", "Net", "Max DD", "Trades", "$/trade", "Months"]

def tile_grid(stats):
    cells = ""
    for k in ORDER:
        if k in stats:
            hot = ' hot' if is_hot(k, stats[k]) else ''
            cells += f'<div class="wtile{hot}"><span class="wk">{esc(k)}</span><span class="wv">{esc(stats[k])}</span></div>'
    for k, v in stats.items():
        if k not in ORDER:
            cells += f'<div class="wtile"><span class="wk">{esc(k)}</span><span class="wv">{esc(v)}</span></div>'
    return f'<div class="wtiles">{cells}</div>'

def windows_block(p, label_prefix=""):
    b, f = p["best"], p["full"]
    out = f'''<div class="winset">
    <div class="win-h"><span class="win-tag win-tag-best">BEST WINDOW</span><span class="win-range">{esc(p.get("window",""))}</span></div>
    {tile_grid(b["stats"])}'''
    if f:
        out += f'''
    <div class="win-h win-h-2"><span class="win-tag">FULL 2024+ WINDOW</span><span class="win-range">context</span></div>
    {tile_grid(f["stats"])}'''
    out += "\n  </div>"
    return out

def engines_block(p):
    e = p["engines"]
    out = ""
    for key, label in [("v1", "ENGINE V1 · INSIDE ENTRY"), ("v2", "ENGINE V2 · EXPANSION-GATED")]:
        d = e[key]
        out += f'''<div class="winset">
    <div class="win-h"><span class="win-tag win-tag-eng">{label}</span><span class="win-range">{esc(d.get("window",""))}</span></div>
    {tile_grid(d["best"]["stats"])}'''
        if d.get("full"):
            out += f'''
    <div class="win-h win-h-2"><span class="win-tag">FULL 2024+ WINDOW</span><span class="win-range">context</span></div>
    {tile_grid(d["full"]["stats"])}'''
        out += "\n  </div>"
    return out

def chart_figure(p):
    b = p["best"]["stats"]
    net, dd, n, win, pf = b.get("Net"), b.get("Max DD"), b.get("Trades"), b.get("Win"), b.get("PF")
    if not net: return ""
    s1 = charts.series(p["slug"], num(net), num(n) or None, num(win) or None, num(pf) or None, num(dd) or None)
    lines, areas, y0 = charts.to_paths([s1])
    zero = f'<line class="czero" x1="0" y1="{y0:.1f}" x2="640" y2="{y0:.1f}"/>' if 10 < y0 < 172 else ""
    return f"""<figure class="chart-panel">
    <div class="chart-head"><span class="chart-title">Cumulative net &middot; best window</span><span class="chart-end">{esc(net)}</span></div>
    <svg viewBox="0 0 640 180" preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <defs><linearGradient id="cg-{p["slug"]}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#56C8A2" stop-opacity=".22"/>
        <stop offset="1" stop-color="#56C8A2" stop-opacity="0"/>
      </linearGradient></defs>
      {zero}<path class="carea" fill="url(#cg-{p["slug"]})" d="{areas[0]}"/><path class="cline" d="{lines[0]}"/>
    </svg>
    <figcaption class="chart-note">Illustrative equity path fitted to the published best-window stats (net, max drawdown, sample size) &mdash; not trade-by-trade equity. X-axis: trade sequence.</figcaption>
  </figure>"""

def calendar_panel():
    cells = "".join('<span class="cal-day"></span>' for _ in range(23))
    return f"""<div class="record">
  <div class="record-title">Daily results calendar</div>
  <div class="cal-grid" aria-hidden="true">
    <span class="cal-wd">M</span><span class="cal-wd">T</span><span class="cal-wd">W</span><span class="cal-wd">T</span><span class="cal-wd">F</span>
    {cells}
  </div>
  <p class="record-note">Awaiting daily P&amp;L export &mdash; each trading day fills green or red with its result.</p>
</div>"""

def rodd_menu(p):
    b = p["best"]["stats"]
    rodd, dd = num(b.get("RoDD", 0)), num(b.get("Max DD", 0))
    months = num(b.get("Months", 0))
    net = b.get("Net", "")
    if not rodd or not dd: return ""
    red_at = dd
    if p["slug"] == "pool-milestone-pullback":
        red_at = max(dd, 12300)  # unfilterable worst session — sizing guard
    slug = p["slug"]
    radios, labels, outs = "", "", ""
    default_set = False
    for i, C in enumerate(NOTCHES, 1):
        if C < red_at: state = "red"
        elif C < 2 * red_at: state = "amb"
        else: state = "ok"
        checked = ""
        if state == "ok" and not default_set:
            checked = " checked"; default_set = True
        proj = rodd * C
        permo = proj / months if months else 0
        lab = f"${C//1000}k" if C >= 1000 and C % 1000 == 0 else f"${C/1000:.1f}k"
        radios += f'<input type="radio" name="ro-{slug}" id="ro-{slug}-{i}" class="ro-r ro-{state}"{checked}>'
        labels += (f'<label for="ro-{slug}-{i}" class="ro-notch"><span class="ro-tick" aria-hidden="true"></span>'
                   f'<span class="ro-amt">{lab}</span></label>')
        if state == "red":
            body = (f'<span class="ro-flag">NOT BUILT FOR THIS SIZE</span> The published max drawdown on this window '
                    f'({usd(red_at)}) exceeds a {lab} budget &mdash; this sizing would not have survived the sample. '
                    f'Some systems are not meant to run this small.')
        else:
            body = (f'A drawdown budget of <b>{lab}</b> historically returned <b>~{usd(proj)}</b> over this window'
                    + (f' (&asymp;{usd(permo)}/mo average)' if permo else '') + '.')
            if state == "amb":
                body = ('<span class="ro-flag">THIN CUSHION</span> The published drawdown is more than half this '
                        'budget &mdash; one bad stretch uses most of your room. ' + body)
        outs += f'<div class="ro-out ro-out-{i}">{body}</div>'
    if not default_set:  # everything red/amber — check the last notch
        radios = radios.replace(f'id="ro-{slug}-{len(NOTCHES)}" class', f'id="ro-{slug}-{len(NOTCHES)}" checked class', 1)
    return f"""<div class="rodd" aria-label="Return-on-drawdown sizing menu">
  <div class="rodd-head">
    <span class="rodd-title">Return on drawdown &middot; what a dollar of pain buys</span>
    <span class="rodd-fig">{esc(b.get("RoDD",""))}&times;</span>
  </div>
  <p class="rodd-why"><b>RoDD is the metric this catalog is priced on.</b> Profit factor says the engine works;
  RoDD says what it costs to hold: net profit divided by the worst peak-to-valley drawdown.
  This system&rsquo;s window: {esc(net)} net &divide; {usd(dd)} max drawdown = <b>{esc(b.get("RoDD",""))}&times;</b>.
  Slide your drawdown budget &mdash; the projection scales with it, and so does the pain.</p>
  {radios}
  <div class="ro-track" aria-hidden="false">{labels}</div>
  <div class="ro-outs">{outs}</div>
  <p class="ro-note">Linear scaling of the published window; not a projection of future results. See the disclaimer below.</p>
</div>"""

def legs_block(p):
    if not p.get("legs"): return ""
    cells = "".join(f'<div class="leg"><span class="leg-n">{i:02d}</span><span class="leg-name">{esc(l)}</span></div>'
                    for i, l in enumerate(p["legs"], 1))
    return f"""<div class="record">
  <div class="record-title">The legs &middot; {len(p["legs"])} engines, one router</div>
  <div class="legs">{cells}</div>
  <p class="record-note">Each leg is a standalone engine; the router allocates them across the session. Composition dials are proprietary.</p>
</div>"""

def sep_block(p):
    if not p.get("sep"): return ""
    items = "".join(f'<li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>{s}</span></li>'
                    for s in p["sep"])
    return f"""<div class="record sep-panel">
  <div class="record-title">What separates this strategy</div>
  <ul class="sep-list">{items}</ul>
</div>"""

def warn_block(p):
    if not p.get("warn"): return ""
    return f"""<div class="warn-box">
  <svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" vector-effect="non-scaling-stroke"/><path d="M12 9v4" vector-effect="non-scaling-stroke"/><path d="M12 17h.01" vector-effect="non-scaling-stroke"/></svg>
  <p>{p["warn"]}</p>
</div>"""

def market_chips(meta):
    first = meta.split("·")[0].strip()
    chips = ""
    for mkt in first.replace("+", " ").split():
        if mkt.isalpha() and mkt.isupper() and 1 < len(mkt) <= 4:
            chips += f'<span class="chip chip-mkt">{mkt}</span>'
    if not chips:
        chips = f'<span class="chip chip-mkt">{esc(first[:6])}</span>'
    return chips

# ── strategy + book pages ───────────────────────────────────────
os.makedirs(os.path.join(BASE, "strategies"), exist_ok=True)
urls = ["/"]

def product_page(p, is_book):
    path = f"/strategies/{p['slug']}.html"
    urls.append(path)
    b = p["best"]["stats"]
    mdesc = (f"{p['name']} ({p['actual']}): RoDD {b.get('RoDD','')} on the published window, "
             f"PF {b.get('PF','')}, {b.get('Trades','')} trades. Live-validated. "
             f"TradingView invite-only script, activated within 24h.")
    crumb_root = ('<a href="/strategies/the-books.html">The Books</a>' if is_book
                  else '<a href="/#strategies">Strategies</a>')
    main_col = chart_figure(p) + "\n" + calendar_panel() + "\n" + (
        engines_block(p) if p.get("engines") else windows_block(p))
    main_col += "\n" + warn_block(p) + "\n" + rodd_menu(p) + "\n" + legs_block(p) + "\n" + sep_block(p)
    xsell = None
    struck = None
    if is_book:
        others = [bk for bk in CAT["books"] if bk["slug"] != p["slug"]]
        xsell = ('All four engines: <a href="/strategies/the-books.html">The Books — $2,999/mo</a> · '
                 + " · ".join(f'<a href="/strategies/{o["slug"]}.html">{esc(o["name"])}</a>' for o in others[:2]))
    page = head(f"{p['name']} — Goal33 Systems", mdesc, path)
    page += f"""
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb">{crumb_root}<span class="sep">/</span>{esc(p['name'])}</nav>

    <article class="pdp">
      <div class="pdp-head">
        <div>
          <h1>{esc(p['name'])}</h1>
          <div class="card-real">{esc(p['actual'])}</div>
          <div class="pdp-meta">{market_chips(p['meta'])}<span class="chip chip-verified">LIVE-VALIDATED</span>{'<span class="chip chip-mkt">IN-HOUSE BOOK</span>' if is_book else ''}</div>
          <span class="pdp-note">{esc(p['meta'])}</span>
        </div>
        <div class="pdp-hero"><b>{esc(b.get('RoDD',''))}&times;</b><span>Return on drawdown &middot; best window</span></div>
      </div>

      <div class="pdp-cols">
        <div class="pdp-main">
        {main_col}
        </div>
        {buybox(p['name'], f"{p['price']:,}", p['name'] + " / " + p['actual'], xsell=xsell)}
      </div>

      <div class="pdp-disclaim">
        <p class="disclaim-sm">{esc(DISCLAIMER)}</p>
      </div>

      <a class="backlink" href="{'/strategies/the-books.html' if is_book else '/#strategies'}">&larr; {'The Books' if is_book else 'All strategies'}</a>
    </article>
  </div>
"""
    page += FOOTER
    open(os.path.join(BASE, "strategies", p["slug"] + ".html"), "w", encoding="utf-8").write(page)

for p in CAT["strategies"]:
    product_page(p, is_book=False)
for p in CAT["books"]:
    product_page(p, is_book=True)

# ── bundle pages ────────────────────────────────────────────────
BN = CAT["bundles"]

def bundle_page(slug, name, price, struck, desc, extra, xsell):
    path = f"/strategies/{slug}.html"
    urls.append(path)
    page = head(f"{name} — Goal33 Systems", desc + " TradingView invite-only scripts, activated within 24h.", path)
    page += f"""
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/#packages">Bundles</a><span class="sep">/</span>{esc(name)}</nav>
    <article class="pdp">
      <div class="pdp-head">
        <div>
          <h1>{esc(name)}</h1>
          <div class="pdp-meta"><span class="chip chip-mkt">BUNDLE</span></div>
          <span class="pdp-note">{esc(desc)}</span>
        </div>
        <div class="pdp-hero"><b>${price:,}</b><span>per month</span></div>
      </div>
      <div class="pdp-cols">
        <div class="pdp-main">
        {extra}
        </div>
        {buybox(name, f"{price:,}", name + " bundle", xsell=xsell, struck=f"{struck:,}" if struck else None)}
      </div>
      <div class="pdp-disclaim"><p class="disclaim-sm">{esc(DISCLAIMER)}</p></div>
      <a class="backlink" href="/#packages">&larr; Bundles</a>
    </article>
  </div>
"""
    page += FOOTER
    open(os.path.join(BASE, "strategies", slug + ".html"), "w", encoding="utf-8").write(page)

inc_rows = "".join(
    f'<li><a class="sys-link" href="/strategies/{s["slug"]}.html"><span class="inc-name">{esc(s["name"])}</span></a>'
    f'<span class="inc-price">${s["price"]}/mo</span></li>'
    for s in sorted(CAT["strategies"], key=lambda x: -x["price"]))
bundle_page("all-access", "All-Access", BN["all_access"]["price"], BN["all_access"]["combined"],
    "Every validated strategy in the catalog. The Books are not included.",
    f"""<div class="record">
        <div class="record-title">Included — all {len(CAT["strategies"])} validated systems (combined ${BN["all_access"]["combined"]:,}/mo)</div>
        <div class="included included-scroll" tabindex="0" role="region" aria-label="All included systems"><ul>{inc_rows}</ul></div>
        <p class="record-note">The Books are not included in All-Access. The four in-house engines are a separate premium tier, from $589/mo each or $2,999/mo together.</p>
      </div>""",
    'Want the engines themselves? <a href="/strategies/the-books.html">The Books — $2,999/mo</a>')

bundle_page("pick-3", "Pick-3", BN["pick3"]["price"], BN["pick3"]["top3"],
    "Any three validated systems, swap monthly.",
    """<div class="record">
        <div class="record-title">How Pick-3 works</div>
        <ul class="included">
          <li><span class="inc-name">Choose any 3 validated systems</span></li>
          <li><span class="inc-name">Swap your picks monthly</span></li>
          <li><span class="inc-name">Each pick delivered as a TradingView invite-only script, activated within 24h</span></li>
        </ul>
      </div>""",
    'Want everything? <a href="/strategies/all-access.html">All-Access — $999/mo</a>')

book_rows = "".join(
    f'<li><a class="sys-link" href="/strategies/{b["slug"]}.html"><span class="inc-name">{esc(b["name"])}</span></a>'
    f'<span class="inc-price">{esc(b["actual"])} · ${b["price"]:,}/mo solo</span></li>'
    for b in CAT["books"])
bundle_page("the-books", "The Books", BN["books_all"]["price"], BN["books_all"]["combined"],
    "All four in-house engines. The metric that matters at this level: return on drawdown.",
    f"""<div class="record">
        <div class="record-title">Included — all four in-house engines</div>
        <ul class="included">{book_rows}</ul>
        <p class="record-note">The engines we run ourselves. Each book is also sold separately; this tier is all four, priced under any two solo.</p>
      </div>""",
    'Not ready for the engines? <a href="/strategies/all-access.html">All-Access — $999/mo</a>')

# ── success page ────────────────────────────────────────────────
psucc = head("Order Confirmed — Goal33 Systems",
             "Purchase confirmed. Your TradingView invite-only script activates within 24h.",
             "/success.html").replace(
    '<meta property="og:type" content="website">',
    '<meta property="og:type" content="website">\n<meta name="robots" content="noindex">')
psucc += f"""
  <div class="wrap">
    <article class="pdp">
      <div class="pdp-head">
        <div>
          <div class="microlabel">Order confirmed</div>
          <h1>You&rsquo;re in.</h1>
          <div class="pdp-meta"><span class="chip chip-verified">PAYMENT RECEIVED</span></div>
          <span class="pdp-note">TradingView invite-only script &middot; activated within 24h</span>
        </div>
      </div>

      <div class="pdp-cols">
        <div class="pdp-main">
          <div class="record">
            <div class="record-title">What happens now</div>
            <table>
              <tbody>
                <tr><th scope="row">01 &middot; Receipt</th><td>Whop has emailed your receipt. Your subscription lives in your Whop dashboard &mdash; manage or cancel it there anytime.</td></tr>
                <tr><th scope="row">02 &middot; TradingView link</th><td>If you entered your TradingView username at checkout, you&rsquo;re set. If not, add it now in your Whop dashboard under this product &mdash; access can&rsquo;t be granted without it.</td></tr>
                <tr><th scope="row">03 &middot; Activation</th><td>Your script is activated within 24h. It appears in TradingView under Indicators &rarr; Invite-only scripts. TradingView also sends a notification &mdash; check spam if you don&rsquo;t see it.</td></tr>
                <tr><th scope="row">04 &middot; Setup</th><td>Load the script on your chart and set alerts using the included templates and setup documentation.</td></tr>
              </tbody>
            </table>
            <p class="record-note">Username must match your TradingView account exactly &mdash; access is granted per username. Nothing arrived after 24h? Email us and we&rsquo;ll grant it manually.</p>
          </div>
        </div>

        <aside class="buybox" aria-label="Support">
          <span class="annual">Need a hand?</span>
          <!--email_off--><a class="btn btn-buy" href="mailto:support@goal33systems.com">Email support</a><!--/email_off-->
          <ul>
            <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Manual activation fallback within the 24h window</span></li>
            <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Cancel anytime from your Whop dashboard</span></li>
          </ul>
          <p class="xsell">Questions first? <a href="/#faq">Read the FAQ</a></p>
        </aside>
      </div>

      <div class="pdp-disclaim">
        <p class="disclaim-sm">{esc(DISCLAIMER)}</p>
      </div>

      <a class="backlink" href="/#strategies">&larr; Browse the catalog</a>
    </article>
  </div>
"""
psucc += FOOTER
open(os.path.join(BASE, "success.html"), "w", encoding="utf-8").write(psucc)

# ── 404 ─────────────────────────────────────────────────────────
p404 = head("404 — Goal33 Systems", "Page not found.", "/404.html").replace(
    '<meta property="og:type" content="website">',
    '<meta property="og:type" content="website">\n<meta name="robots" content="noindex">')
p404 += f"""
  <div class="wrap err-wrap">
    <div class="err">
      <h1 class="err-code">404<span class="sr-only"> — page not found</span></h1>
      <div class="term">
        <div class="term-bar"><span>g33 · locate</span><span>bash</span></div>
        <div class="term-body">
          <div class="cmd">g33 locate ./requested-page</div>
          <div class="out">searching catalog ...... <span class="num">{len(CAT["strategies"]) + len(CAT["books"])} products</span></div>
          <div class="out">match .................. no such system</div>
          <div class="out">status ................. <span class="ok">the rest of the site is intact</span></div>
          <div class="cmd"><span class="cursor"></span></div>
        </div>
      </div>
      <div class="err-links">
        <a class="btn btn-solid" href="/">Back to Goal33</a>
        <a class="btn" href="/#strategies">Browse strategies</a>
      </div>
    </div>
  </div>
"""
p404 += FOOTER
open(os.path.join(BASE, "404.html"), "w", encoding="utf-8").write(p404)

# ── sitemap + stale-page cleanup ────────────────────────────────
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    sm += f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n"
sm += "</urlset>\n"
open(os.path.join(BASE, "sitemap.xml"), "w", encoding="utf-8").write(sm)

keep = {u.rsplit("/", 1)[-1] for u in urls if u.startswith("/strategies/")}
removed = []
for f in os.listdir(os.path.join(BASE, "strategies")):
    if f.endswith(".html") and f not in keep:
        os.remove(os.path.join(BASE, "strategies", f))
        removed.append(f)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print(f"wrote {len(urls)-1} product/bundle pages + success + 404 + sitemap ({len(urls)} urls)")
if removed:
    print("removed stale pages:", ", ".join(sorted(removed)))
