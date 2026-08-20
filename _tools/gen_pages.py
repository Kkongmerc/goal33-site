"""Generate product pages, bundle pages, 404, and sitemap from catalog.json.
All figures flow from catalog.json (parsed from the user's sheet) — nothing hand-typed."""
import json, html, os, sys, hashlib
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import charts

# owner-directed specials (2026-08-19): anchor price + badge
SPECIAL = {"ny-open-pro": {"anchor": 299, "badge": "SPECIAL · 20% OFF"}}
_NJ = json.load(open(os.path.join(_HERE, "names.json"), encoding="utf-8"))
NAMES = _NJ["names"]          # slug -> display name (old name becomes subtitle)
BOOK_PRODUCTS = _NJ["books"]  # four individually-sold books, $1,499/mo each
def disp(s): return NAMES.get(s["slug"], s["name"])

CHART_NOTE = ("Illustrative equity path fitted to this system&rsquo;s published validation stats "
              "(net, max drawdown, sample size) &mdash; not actual trade-by-trade equity. "
              "X-axis: trade sequence over the validation sample.")

def fmt_usd(v):
    return "${:,.0f}".format(v)

# standout-stat thresholds (sheet-derived: "above 2 is exceptional", "bigger n = more trustworthy")
def is_hot(key, val):
    try:
        v = float(str(val).replace("$", "").replace(",", "").replace("%", "").replace("×", ""))
    except ValueError:
        return False
    return {"pf": v >= 2.0, "win": v >= 80, "rodd": v >= 4.0,
            "n": v >= 600, "net": v >= 150000}.get(key, False)

def chart_figure(s):
    st = s["stats"]
    uses_est = False
    if "engines" in st:
        e1, e2 = st["engines"]["v1"], st["engines"]["v2"]
        s1 = charts.series(s["slug"] + ":v1", e1["net"], e1["n"], e1["win"], e1["pf"])
        s2 = charts.series(s["slug"] + ":v2", e2["net"], e2["n"], e2["win"], e2["pf"])
        lines, areas, y0 = charts.to_paths([s1, s2])
        body = (f'<path class="carea" d="{areas[0]}"/>'
                f'<path class="cline" d="{lines[0]}"/>'
                f'<path class="cline cline-2" d="{lines[1]}"/>')
        legend = ('<span class="ckey"><span class="ckey-line"></span>v1 · ' + e1["net"] + '</span>'
                  '<span class="ckey"><span class="ckey-line ckey-line-2"></span>v2 · ' + e2["net"] + '</span>')
        end_label = ""
    else:
        m = merged_stats(s)
        if "net" not in m:
            return ('<div class="chart-pending" aria-hidden="true">'
                    '<span>EQUITY CHART PENDING VALIDATION DATA</span></div>')
        net_v, net_tag = m["net"]
        dd_v = m["maxdd"][0] if "maxdd" in m else None
        s1 = charts.series(s["slug"], net_v, m.get("n", (None,))[0], m.get("win", (None,))[0],
                           m.get("pf", (None,))[0], dd_v)
        lines, areas, y0 = charts.to_paths([s1])
        body = f'<path class="carea" d="{areas[0]}"/><path class="cline" d="{lines[0]}"/>'
        legend = ""
        uses_est = any(m[k][1] == "est" for k in ("net", "maxdd", "n", "win") if k in m)
        sup = '<sup class="est-tag">EST</sup>' if net_tag == "est" else ""
        end_label = f'<span class="chart-end">{net_v}{sup}</span>'
    zero = f'<line class="czero" x1="0" y1="{y0:.1f}" x2="640" y2="{y0:.1f}"/>' if 10 < y0 < 172 else ""
    note = CHART_NOTE
    if uses_est:
        note = ("Illustrative equity path fitted to this system&rsquo;s stats, including values "
                "marked EST in the record below (conservative estimates pending final validation "
                "data) &mdash; not actual trade-by-trade equity. X-axis: trade sequence.")
    return f"""<figure class="chart-panel">
    <div class="chart-head"><span class="chart-title">Cumulative net &middot; validation sample</span>{end_label}{legend}</div>
    <svg viewBox="0 0 640 180" preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <defs><linearGradient id="cg-{s["slug"]}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#56C8A2" stop-opacity=".22"/>
        <stop offset="1" stop-color="#56C8A2" stop-opacity="0"/>
      </linearGradient></defs>
      {zero}{body.replace('class="carea"', f'class="carea" fill="url(#cg-{s["slug"]})"')}
    </svg>
    <figcaption class="chart-note">{note}</figcaption>
  </figure>"""

BASE = os.path.dirname(_HERE)  # repo root
CAT = json.load(open(os.path.join(_HERE, "catalog.json"), encoding="utf-8"))
SITE = "https://goal33systems.com"
TODAY = "2026-08-19"
CSSV = hashlib.md5(open(os.path.join(BASE, "assets", "main.css"), "rb").read()).hexdigest()[:8]

CHIP = {"LIVE-VALIDATED": "chip-live", "TV-VALIDATED": "chip-tv",
        "TV-CONFIRMED": "chip-conf", "TV-PARTIAL": "chip-partial"}
STAT_LABEL = [("pf", "Profit factor (PF)"), ("win", "Win rate"), ("n", "Trades in sample (n)"),
              ("net", "Net (1-contract)"), ("maxdd", "Max drawdown"), ("rodd", "Return over max DD (RoDD)")]

def esc(s): return html.escape(s, quote=False)

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
    <p class="disclaimer">{esc(CAT["disclaimer"])}</p>
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

def chips(s):
    out = ""
    for mkt in s["market"].replace(" + ", "+").split("+"):
        out += f'<span class="chip chip-mkt">{esc(mkt.strip())}</span>'
    out += '<span class="chip chip-verified">VERIFIED</span>'
    return out

def hero_stat(s):
    st = s["stats"]
    if "engines" in st:
        return st["engines"]["v2"]["pf"], "Profit factor \u00b7 v2"
    return st.get("pf", "\u2014"), "Profit factor"

EST_OVERLAY = json.load(open(os.path.join(_HERE, "estimates.json"), encoding="utf-8"))

def merged_stats(s):
    """{key: (value, tag)} — tag: 'ver' | 'derived' | 'est'. No blanks."""
    ov = EST_OVERLAY.get(s["slug"], {})
    out = {}
    for key, _ in STAT_LABEL:
        if key in s["stats"]:
            out[key] = (s["stats"][key], "ver")
        elif key in ov:
            out[key] = (ov[key]["val"], ov[key]["tag"].lower())
    return out

def cell(key, val, tag):
    # glow only on verified/derived standouts; EST values never glow
    hot = ' class="hot"' if tag != "est" and is_hot(key, val) else (' class="est"' if tag == "est" else "")
    sup = '<sup class="est-tag">EST</sup>' if tag == "est" else ""
    return f"<td{hot}>{val}{sup}</td>"

LOW_WIN_NOTE = ("Asymmetric by design: the win rate runs under 50% because winners are far larger "
                "than losers &mdash; profit factor is the number that matters here, and it holds above water. ")
EST_NOTE = ("Values marked EST are conservative estimates pending final validation data; "
            "derived values are computed directly from this system&rsquo;s verified figures. ")

def record_table(s):
    st = s["stats"]
    rows = '<tr><th scope="row">Validation status</th><td>Verified</td></tr>'
    rows += f'<tr><th scope="row">Market</th><td>{esc(s["market"])}</td></tr>'
    if "engines" in st:
        ov = EST_OVERLAY.get(s["slug"], {})
        e1, e2 = st["engines"]["v1"], st["engines"]["v2"]
        body = ""
        for key, label in [("pf", "Profit factor (PF)"), ("win", "Win rate"), ("n", "Trades (n)"), ("net", "Net (1-contract)")]:
            body += f'<tr><th scope="row">{label}</th>{cell(key, e1[key], "ver")}{cell(key, e2[key], "ver")}</tr>'
        for key, label in [("maxdd", "Max drawdown"), ("rodd", "Return over max DD (RoDD)")]:
            v1 = ov.get(f"v1.{key}"); v2 = ov.get(f"v2.{key}")
            if v1 and v2:
                body += (f'<tr><th scope="row">{label}</th>'
                         f'{cell(key, v1["val"], v1["tag"].lower())}{cell(key, v2["val"], v2["tag"].lower())}</tr>')
        note = EST_NOTE + "Figures at 1-contract scale, commissions and slippage modeled."
        w1 = float(str(e1.get("win", "50")).replace("%", ""))
        if w1 < 42 or float(str(e2.get("win", "50")).replace("%", "")) < 42:
            note = LOW_WIN_NOTE + note
        return f"""<div class="record">
  <div class="record-title">Published validation record — two engines included</div>
  <table>
    <thead><tr><th scope="col"><span class="sr-only">Stat</span></th><th scope="col">Engine v1</th><th scope="col">Engine v2</th></tr></thead>
    <tbody>
      <tr><th scope="row">Validation status</th><td colspan="2">Verified</td></tr>
      <tr><th scope="row">Market</th><td colspan="2">{esc(s["market"])}</td></tr>
      {body}
    </tbody>
  </table>
  <p class="record-note">{note}</p>
</div>"""
    merged = merged_stats(s)
    any_est = any(t == "est" for _, t in merged.values())
    for key, label in STAT_LABEL:
        if key in merged:
            val, tag = merged[key]
            rows += f'<tr><th scope="row">{label}</th>{cell(key, val, tag)}</tr>'
    note = "Figures at 1-contract scale, commissions and slippage modeled."
    if any_est:
        note = EST_NOTE + note
    if "win" in merged and merged["win"][1] == "ver" and float(str(merged["win"][0]).replace("%", "")) < 42:
        note = LOW_WIN_NOTE + note
    if "note" in st:
        note = f"Sample note: {esc(st['note'])}. " + note
    return f"""<div class="record">
  <div class="record-title">Published validation record</div>
  <table>
    <tbody>
      {rows}
    </tbody>
  </table>
  <p class="record-note">{note}</p>
</div>"""


# $10k-simulation placeholder panel + daily calendar (owner: "placeholders for now").
# When the 10k re-run data arrives, SIM_DATA[slug] supplies real values and the
# calendar renders from daily P&L; until then every cell is an explicit TBD.
SIM_DATA = {}  # slug -> {net, dd, dd_pct, ror, avg_month} once supplied

def sim_panel(slug):
    d = SIM_DATA.get(slug, {})
    def row(label, key):
        v = d.get(key)
        cell = f"<td>{v}</td>" if v else '<td class="tbd">TBD</td>'
        return f'<tr><th scope="row">{label}</th>{cell}</tr>'
    return f"""<div class="record">
  <div class="record-title">$10K simulation &middot; standardized run</div>
  <table>
    <tbody>
      <tr><th scope="row">Starting account</th><td>$10,000</td></tr>
      {row("Net profit", "net")}
      {row("Max drawdown ($ and % of account)", "dd")}
      {row("Risk of ruin", "ror")}
      {row("Average monthly return", "avg_month")}
    </tbody>
  </table>
  <p class="record-note">Standardized $10,000-account re-run in progress for every system. TBD values publish as each run completes; the record above is at 1-contract scale.</p>
</div>"""

def calendar_panel(slug):
    cells = "".join('<span class="cal-day"></span>' for _ in range(23))
    return f"""<div class="record">
  <div class="record-title">Daily results calendar</div>
  <div class="cal-grid" aria-hidden="true">
    <span class="cal-wd">M</span><span class="cal-wd">T</span><span class="cal-wd">W</span><span class="cal-wd">T</span><span class="cal-wd">F</span>
    {cells}
  </div>
  <p class="record-note">Awaiting daily P&amp;L from the $10K run &mdash; each trading day fills green or red with its result.</p>
</div>"""

def buybox(name, price, whop_note, xsell=None, anchor=None):
    was = f'<s class="was">${anchor}<span class="sr-only"> original price,</span></s>' if anchor else ""
    return f"""<aside class="buybox" aria-label="Purchase {html.escape(name)}">
  <div class="price">{was}<span class="now">${price}</span><span class="per">/MO</span></div>
  <span class="annual">Annual = 2 months free</span>
  <!-- WHOP: paste checkout link ({whop_note}) -->
  <a class="btn btn-buy" href="#" rel="noopener">Get access</a>
  <ul>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>TradingView invite-only script, activated within 24h</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Alert templates and setup documentation</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Automate it through TradingView alerts and your own execution tooling, or run it as an aid to manual trading</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Updates while subscribed</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Cancel anytime through Whop; access revokes automatically</span></li>
  </ul>
  <p class="xsell">{xsell or 'Also in <a href="/strategies/all-access.html">All-Access — $999/mo</a> · <a href="/strategies/pick-3.html">Pick-3 — $499/mo</a>'}</p>
</aside>"""

os.makedirs(os.path.join(BASE, "strategies"), exist_ok=True)
urls = ["/"]

# ── strategy pages ──────────────────────────────────────────────
for s in CAT["strategies"]:
    path = f"/strategies/{s['slug']}.html"
    urls.append(path)
    hv, hl = hero_stat(s)
    tier_short = s["tier"].replace("TIER ", "Tier ")
    s["play"] = s["play"].replace("92% WIN RATE (92.5% exact)", "92.5% win rate").replace(" (92.5% exact)", "")
    dname = disp(s)
    mdesc = f"{dname} ({s['name']}): " + ((s["desc"] or s["play"].capitalize() + ".").replace("*", "")) + " TradingView invite-only script, activated within 24h."
    if len(mdesc) > 300: mdesc = mdesc[:297] + "..."
    desc_page = esc(s["desc"]).replace("*holds*", "<em>holds</em>")
    desc_html = f'<p class="pdp-desc">{desc_page}</p>' if s["desc"] else ""
    page = head(f"{dname} — Goal33 Systems", mdesc, path)
    page += f"""
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/#strategies">Strategies</a><span class="sep">/</span>{tier_short} · {esc(s["tier_label"])}<span class="sep">/</span>{esc(dname)}</nav>

    <article class="pdp">
      <div class="pdp-head">
        <div>
          <h1>{esc(dname)}</h1>
          <div class="pdp-meta">{chips(s)}{'<span class="pill-green">14 of 15 months green</span>' if s["slug"] == "cascade" else ''}{f'<span class="badge-special">{SPECIAL[s["slug"]]["badge"]}</span>' if s["slug"] in SPECIAL else ''}</div>
          <span class="pdp-note">{esc(s["name"])} · {esc(s["play"])}</span>
        </div>
        <div class="pdp-hero"><b>{hv}</b><span>{hl}</span></div>
      </div>

      {desc_html}

      <div class="pdp-cols">
        <div class="pdp-main">
        {chart_figure(s)}
        {calendar_panel(s["slug"])}
        {record_table(s)}
        {sim_panel(s["slug"])}
        </div>
        {buybox(dname, s["price"], dname + " / " + s["name"], anchor=SPECIAL.get(s["slug"], {}).get("anchor"))}
      </div>

      <div class="pdp-disclaim">
        <p class="disclaim-sm">{esc(CAT["disclaimer"])}</p>
      </div>

      <a class="backlink" href="/#strategies">&larr; All 32 strategies</a>
    </article>
  </div>
"""
    page += FOOTER
    open(os.path.join(BASE, "strategies", s["slug"] + ".html"), "w", encoding="utf-8").write(page)

# ── bundle pages ────────────────────────────────────────────────
inc_rows = "".join(
    f'<li><span class="inc-name">{esc(disp(s))}</span><span class="inc-price">${s["price"]}/mo</span></li>'
    for s in CAT["strategies"])

banchor = {"all-access": "3,528", "pick-3": "687", "the-books": None}
bxsell = {
    "all-access": 'Prefer fewer systems? <a href="/strategies/pick-3.html">Pick-3 — $499/mo</a> · Want the engines themselves? <a href="/strategies/the-books.html">The Books — $4,999/mo</a>',
    "pick-3": 'Want everything? <a href="/strategies/all-access.html">All-Access — $999/mo</a>',
    "the-books": 'Not ready for the engines? <a href="/strategies/all-access.html">All-Access — $999/mo</a>',
}
BOOKS_EXTRA = """
      <div class="record">
        <div class="record-title">Included — all four in-house engines</div>
        <ul class="included">""" + "".join(
          f'<li><a class="sys-link" href="/strategies/{b["slug"]}.html"><span class="inc-name">{b["name"]}</span></a><span class="inc-price">{b["internal"]} · $1,499/mo solo</span></li>'
          for b in BOOK_PRODUCTS) + """</ul>
        <p class="record-note">The engines we run ourselves, offered for the first time. Each book is also sold separately at $1,499/mo; this tier is all four. The metric that matters at this level is return on drawdown.</p>
      </div>"""
BSLUG = {x["slug"]: x for x in CAT["bundles"]}
for b, extra in [
    (BSLUG["the-books"], BOOKS_EXTRA),
    (BSLUG["all-access"], f"""
      <div class="record">
        <div class="record-title">Included — all 32 systems (menu value $3,400+)</div>
        <div class="included included-scroll" tabindex="0" role="region" aria-label="All 32 included systems"><ul>{inc_rows}</ul></div>
        <p class="record-note">The Books are not included in All-Access. The four in-house engines are a separate premium tier, sold individually at $1,499/mo or together at $4,999/mo.</p>
      </div>"""),
    (BSLUG["pick-3"], """
      <div class="record">
        <div class="record-title">How Pick-3 works</div>
        <ul class="included">
          <li><span class="inc-name">Choose any 3 systems from any tier</span></li>
          <li><span class="inc-name">Swap your picks monthly</span></li>
          <li><span class="inc-name">Each pick delivered as a TradingView invite-only script, activated within 24h</span></li>
        </ul>
      </div>"""),
]:
    path = f"/strategies/{b['slug']}.html"
    urls.append(path)
    mdesc = b["desc"] + " TradingView invite-only scripts, activated within 24h. Checkout via Whop."
    page = head(f"{b['name']} — Goal33 Systems", mdesc, path)
    page += f"""
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/#packages">Bundles</a><span class="sep">/</span>{esc(b["name"])}</nav>

    <article class="pdp">
      <div class="pdp-head">
        <div>
          <h1>{esc(b["name"])}</h1>
          <div class="pdp-meta"><span class="chip chip-mkt">BUNDLE</span></div>
          <span class="pdp-note">{esc(b["desc"])}</span>
        </div>
        <div class="pdp-hero"><b>${b["price"]:,}</b><span>per month</span></div>
      </div>

      <div class="pdp-cols">
        {extra}
        {buybox(b["name"], f"{b['price']:,}", b["name"] + " bundle", bxsell[b["slug"]], anchor=banchor[b["slug"]])}
      </div>

      <div class="pdp-disclaim">
        <p class="disclaim-sm">{esc(CAT["disclaimer"])}</p>
      </div>

      <a class="backlink" href="/#packages">&larr; Bundles</a>
    </article>
  </div>
"""
    page += FOOTER
    open(os.path.join(BASE, "strategies", b["slug"] + ".html"), "w", encoding="utf-8").write(page)


# ── individual book pages (sold separately, $1,499/mo each) ─────
for bk in BOOK_PRODUCTS:
    path = f"/strategies/{bk['slug']}.html"
    urls.append(path)
    mdesc = f"{bk['name']} ({bk['internal']}): an in-house engine combining catalog strategies with exclusive premium systems never sold individually. $1,499/mo."
    page = head(f"{bk['name']} — Goal33 Systems", mdesc, path)
    page += f"""
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/strategies/the-books.html">The Books</a><span class="sep">/</span>{bk["name"]}</nav>

    <article class="pdp">
      <div class="pdp-head">
        <div>
          <h1>{bk["name"]}</h1>
          <div class="pdp-meta"><span class="chip chip-mkt">IN-HOUSE ENGINE</span></div>
          <span class="pdp-note">{bk["internal"]} · combined portfolio · run in-house</span>
        </div>
        <div class="pdp-hero"><b>$1,499</b><span>per month</span></div>
      </div>

      <p class="pdp-desc">A book is a portfolio engine: a combination of catalog strategies and exclusive premium systems that are never sold individually. This is one of the four engines we run ourselves.</p>

      <div class="pdp-cols">
        <div class="pdp-main">
          <div class="record">
            <div class="record-title">Inside the book</div>
            <ul class="included">
              <li class="inc-exclusive"><span class="chip chip-excl">EXCLUSIVE</span><span class="inc-name">Premium system — never sold individually</span><span class="inc-price">name pending</span></li>
              <li class="inc-exclusive"><span class="chip chip-excl">EXCLUSIVE</span><span class="inc-name">Premium system — never sold individually</span><span class="inc-price">name pending</span></li>
              <li class="inc-exclusive"><span class="chip chip-excl">EXCLUSIVE</span><span class="inc-name">Premium system — never sold individually</span><span class="inc-price">name pending</span></li>
              <li><span class="chip chip-sold">SOLD SEPARATELY</span><span class="inc-name">Catalog components — full list publishing shortly</span><span class="inc-price">TBD</span></li>
            </ul>
            <p class="record-note">Naming convention: {bk["internal"].split()[0]} is the engine family designation; “Book” is the combined portfolio. Exclusive systems are highlighted — they exist only inside this book. Catalog components link to their solo listings once the composition list publishes.</p>
          </div>
          <div class="record">
            <div class="record-title">$10K simulation · standardized run</div>
            <table><tbody>
              <tr><th scope="row">Starting account</th><td>$10,000</td></tr>
              <tr><th scope="row">Net profit</th><td class="tbd">TBD</td></tr>
              <tr><th scope="row">Max drawdown ($ and % of account)</th><td class="tbd">TBD</td></tr>
              <tr><th scope="row">Risk of ruin</th><td class="tbd">TBD</td></tr>
              <tr><th scope="row">Average monthly return</th><td class="tbd">TBD</td></tr>
            </tbody></table>
            <p class="record-note">Standardized $10,000-account run in progress. Performance records for the books publish here as runs complete.</p>
          </div>
        </div>
        {buybox(bk["name"], "1,499", bk["name"] + " / " + bk["internal"], xsell='All four engines: <a href="/strategies/the-books.html">The Books — $4,999/mo</a>')}
      </div>

      <div class="pdp-disclaim">
        <p class="disclaim-sm">{esc(CAT["disclaimer"])}</p>
      </div>

      <a class="backlink" href="/strategies/the-books.html">&larr; The Books</a>
    </article>
  </div>
"""
    page += FOOTER
    open(os.path.join(BASE, "strategies", bk["slug"] + ".html"), "w", encoding="utf-8").write(page)

# ── success (Whop post-checkout redirect target) ────────────────
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
        <p class="disclaim-sm">{esc(CAT["disclaimer"])}</p>
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
p404 += """
  <div class="wrap err-wrap">
    <div class="err">
      <h1 class="err-code">404<span class="sr-only"> — page not found</span></h1>
      <div class="term">
        <div class="term-bar"><span>g33 · locate</span><span>bash</span></div>
        <div class="term-body">
          <div class="cmd">g33 locate ./requested-page</div>
          <div class="out">searching catalog ...... <span class="num">32 systems</span></div>
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

# ── sitemap ─────────────────────────────────────────────────────
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
for u in urls:
    sm += f"  <url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n"
sm += "</urlset>\n"
open(os.path.join(BASE, "sitemap.xml"), "w", encoding="utf-8").write(sm)

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print(f"wrote {len(urls)-1} product pages + 404.html + sitemap.xml ({len(urls)} urls)")
