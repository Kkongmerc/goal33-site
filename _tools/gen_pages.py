"""Generate product pages, bundle pages, success, 404, and sitemap from catalog2.json.
catalog2.json is curated from the owners' validation playbook — every figure on every
page traces to it. Never hand-edit generated pages; edit the catalog or this template."""
import json, html, os, re, sys, hashlib
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import charts
from glyphs import glyph, emblem

BASE = os.path.dirname(_HERE)  # repo root
CAT = json.load(open(os.path.join(_HERE, "catalog2.json"), encoding="utf-8"))
SITE = "https://futurestradingbots.com"
# PRE-LAUNCH: no published products -> skip product + bundle pages entirely
PRELAUNCH = not CAT["strategies"] and not CAT["books"]
WHOP_STORE = CAT.get("whop_store") or "/#packages"
def buy_href(p):
    """The product's Whop page when it has one, else its own page."""
    return p.get("whop") or f"/strategies/{p['slug']}.html"
HAS_BUNDLES = bool(CAT["strategies"])          # All-Access needs strategies only
HAS_BOOKS_BUNDLE = bool(CAT["books"])         # The Books needs books
HAS_STARTER = bool(CAT["bundles"].get("starter", {}).get("slugs")) and all(
    s in {x["slug"] for x in CAT["strategies"]}
    for s in CAT["bundles"].get("starter", {}).get("slugs", []))
TODAY = __import__("datetime").date.today().isoformat()
CSSV = hashlib.md5(open(os.path.join(BASE, "assets", "main.css"), "rb").read()).hexdigest()[:8]

DISCLAIMER = ("All performance figures are backtested or validation-run results shown with commissions and "
              "slippage modeled, on the stated window. Backtested performance is hypothetical, does not "
              "represent live trading results, and is not a guarantee or projection of future returns. Futures "
              "trading involves substantial risk of loss and is not suitable for all investors. Nothing on this "
              "site is financial advice. Access provides the strategy tool only; you are responsible for your "
              "own trading decisions.")

NOTCHES = [1000, 2500, 5000, 10000, 25000, 50000]

def load_trades_data(slug):
    """Real closed-trade data ingested from the validation archive (derived
    numbers only — no settings, no research identifiers)."""
    p = os.path.join(_HERE, "trades", slug + ".json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))

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
def head(title, desc, path, bodycls=""):
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
<meta property="og:site_name" content="FuturesTradingBots">
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
<body{f' class="{bodycls}"' if bodycls else ''}>
<a class="skip" href="#main">Skip to content</a>

<header>
  <div class="wrap nav">
    <a class="brand" href="/"><svg class="bmark" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path class="bmark-ant" d="M12 3.6V7.2"/><circle class="bmark-node" cx="12" cy="2.4" r="1.5"/><rect class="bmark-head" x="3.6" y="7.2" width="16.8" height="13" rx="3.4"/><rect class="bmark-eye" x="8" y="10.3" width="2.3" height="6.4" rx="1.15"/><rect class="bmark-eye" x="13.7" y="11.9" width="2.3" height="4.6" rx="1.15"/></svg><span class="bname">FUTURES<small>TRADING<span class="mk">BOTS</span></small></span></a>
    <nav class="nav-links" aria-label="Main">
      <div class="nav-drop">
        <a href="/#strategies">Strategies<svg class="nav-caret" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></a>
        <div class="nav-menu">
          <a href="/#flagships"><b>Tier 1</b> Flagships</a>
          <a href="/#edge">Browse by edge</a>
          <a href="/#packages">Bundles &amp; deals</a>
        </div>
      </div>
      <a class="nav-books" href="/#packages">Books and Bundles<span class="nav-ember" aria-hidden="true"></span></a>
      <a class="nav-plan" href="/plan.html">Find your plan</a>
      <a href="/#how">How access works</a>
      <a href="/#faq">FAQ</a>
    </nav>
    <!-- WHOP: storefront -->
    <a class="btn btn-sm btn-buy" href="{WHOP_STORE}" rel="noopener">Get access</a>
    <!-- DISCORD: community invite -->
    <a class="btn btn-sm btn-discord" href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener"><svg class="ic-discord" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.7 17.4c-3.2-.1-4.9-1.7-4.9-1.7.3-4 1.4-6.6 2.7-8.3C7.8 6.4 9.2 6 9.2 6l.5 1.1c1.5-.3 3.1-.3 4.6 0L14.8 6s1.4.4 2.7 1.4c1.3 1.7 2.4 4.3 2.7 8.3 0 0-1.7 1.6-4.9 1.7l-.8-1.1c-1.6.3-3.4.3-5 0z"/><circle cx="9.6" cy="12.6" r="1.15" fill="currentColor" stroke="none"/><circle cx="14.4" cy="12.6" r="1.15" fill="currentColor" stroke="none"/></svg><span>Discord</span></a>
    <details class="nav-mob">
      <summary aria-label="Menu"><span class="burger" aria-hidden="true"><i></i><i></i><i></i></span></summary>
      <nav class="nav-mob-panel" aria-label="Mobile">
        <a href="/#strategies">Strategies</a>
        <a href="/#flagships">Tier 1 &middot; Flagships</a>
        <a class="mob-books" href="/#packages">Books and Bundles</a>
        <a href="/plan.html">Find your plan</a>
        <a href="/#how">How access works</a>
        <a href="/#faq">FAQ</a>
        <!-- DISCORD: community invite -->
        <a href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener">Join the community Discord</a>
      </nav>
    </details>
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
      <a href="/plan.html">Find your plan</a>
      <a href="/#how">How access works</a>
      <a href="/terms.html">Terms</a>
      <a href="/privacy.html">Privacy</a>

      <!-- DISCORD: community invite -->
      <a class="foot-discord" href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener"><svg class="ic-discord" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.7 17.4c-3.2-.1-4.9-1.7-4.9-1.7.3-4 1.4-6.6 2.7-8.3C7.8 6.4 9.2 6 9.2 6l.5 1.1c1.5-.3 3.1-.3 4.6 0L14.8 6s1.4.4 2.7 1.4c1.3 1.7 2.4 4.3 2.7 8.3 0 0-1.7 1.6-4.9 1.7l-.8-1.1c-1.6.3-3.4.3-5 0z"/><circle cx="9.6" cy="12.6" r="1.15" fill="currentColor" stroke="none"/><circle cx="14.4" cy="12.6" r="1.15" fill="currentColor" stroke="none"/></svg><span>Join the Community!</span></a>
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
      of hindsight. FuturesTradingBots is a software publisher. Nothing on this site constitutes financial,
      investment, legal, or tax advice, or a solicitation to buy or sell any financial instrument. Purchases,
      billing, and subscription management are processed by Whop; TradingView is a trademark of TradingView, Inc.
    </p>
    <div class="copyright">© 2026 FuturesTradingBots · futurestradingbots.com</div>
  </div>
</footer>

</body>
</html>
"""

def buybox(name, price, whop_note, xsell=None, struck=None, href="#"):
    was = f'<s class="was">${struck}<span class="sr-only"> combined value,</span></s>' if struck else ""
    xs = xsell or (('Everything at once: <a href="/strategies/all-access.html">All-Access — $999/mo</a>') if HAS_BUNDLES else
                   'More systems join the shelf as they clear validation.')
    return f"""<aside class="buybox" aria-label="Purchase {html.escape(name)}">
  <div class="price">{was}<span class="now">${price}</span><span class="per">/MO</span></div>
  <span class="annual">Annual = 2 months free</span>
  <!-- WHOP: checkout ({whop_note}) -->
  <a class="btn btn-buy" href="{href}" rel="noopener">Get access</a>
  <div class="guar">
    <span class="guar-line"><b>7-day</b> money-back &mdash; no questions</span>
    <span class="guar-line"><b>First month not profitable?</b> Full refund</span>
    <span class="guar-note">per the strategy&rsquo;s own published signals &middot; claim within 7 days of day 30 &middot; <a href="/terms.html">terms</a></span>
  </div>
  <ul>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>TradingView invite-only script, activated within 24h</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Alert templates and setup documentation</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Automate it through TradingView alerts and your own execution tooling, or run it as an aid to manual trading</span></li>
    <li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>Cancel anytime through Whop; access revokes automatically</span></li>
  </ul>
  <p class="xsell">{xs}</p>
  <p class="refnote">Have a referral code? It takes <b>10% off</b> at checkout.</p>
</aside>"""

# ── components ──────────────────────────────────────────────────
ORDER = ["RoDD", "RoDD/mo", "PF", "Win", "Net", "Max DD", "Trades", "$/trade", "Months"]

def tile_grid(stats):
    cells = ""
    for k in ORDER:
        if k in stats:
            hot = ' hot' if is_hot(k, stats[k]) else ''
            if k == "Max DD":
                n = num(stats[k])
                hot += ' dd-gold' if n <= 2000 else (' dd-neon' if n <= 5000 else '')
            cells += f'<div class="wtile{hot}"><span class="wk">{esc(k)}</span><span class="wv">{esc(stats[k])}</span></div>'
    for k, v in stats.items():
        if k not in ORDER:
            cells += f'<div class="wtile"><span class="wk">{esc(k)}</span><span class="wv">{esc(v)}</span></div>'
    return f'<div class="wtiles">{cells}</div>'

TVT_ROWS = [("Net profit", "Net"), ("Total closed trades", "Trades"), ("Percent profitable", "Win"),
            ("Profit factor", "PF"), ("Max drawdown", "Max DD"), ("Avg per trade", "$/trade"),
            ("Return on max drawdown", "RoDD"), ("RoDD per month", "RoDD/mo"), ("Months in window", "Months")]

def tvt_val(stats, key, best=False):
    v = stats.get(key, "")
    if v in ("", None): return '<td class="tv-mut">&mdash;</td>'
    cls = "tv-pos" if key in ("Net", "PF", "Win", "RoDD", "RoDD/mo", "$/trade") else ("tv-neg" if key == "Max DD" else "")
    if key == "Max DD" and best:
        n2 = num(v)
        cls += " dd-gold" if n2 <= 2000 else (" dd-neon" if n2 <= 5000 else "")
    return f'<td class="{cls}">{esc(v)}</td>'

HELD_FULL = {
    "< 10m": "held less than 10 minutes", "< 30m": "held less than 30 minutes",
    "< 1h": "held less than an hour", "1-2h": "held approx. 1-2 hours",
    "2-4h": "held approx. 2-4 hours", "4-12h": "held approx. 4-12 hours",
    "12h+": "held over 12 hours",
}

def trades_table(tr, slug):
    """Entries, exits, the trade's net, and a running account ledger.
    The ledger is cumulative net from zero - the record carries no opening
    balance, so starting anywhere else would be inventing a number."""
    rows = ""
    n = len(tr["trades"])
    # walk forward to accumulate, then render newest-first
    running, ledger = 0.0, []
    for day, epx, xpx, pnl in tr["trades"]:
        running += pnl
        ledger.append(running)
    for i in range(n - 1, -1, -1):
        day, epx, xpx, pnl = tr["trades"][i]
        cls = "tv-pos" if pnl > 0 else ("tv-neg" if pnl < 0 else "")
        acc = ledger[i]
        acls = "tv-pos" if acc > 0 else ("tv-neg" if acc < 0 else "")
        rows += (f'<tr><td>{i + 1}</td><td>{esc(day)}</td>'
                 f'<td>{epx if epx is not None else "&mdash;"}</td>'
                 f'<td>{xpx if xpx is not None else "&mdash;"}</td>'
                 f'<td class="{cls}">${pnl:,.2f}</td>'
                 f'<td class="lt-acc {acls}">${acc:,.2f}</td></tr>')
    return f"""<div class="tvt-pane tvt-lt">
    <div class="screener lt-scroll" tabindex="0" role="region" aria-label="Trade log, scrolls">
    <table class="tvt-table lt-table">
      <caption class="sr-only">Every closed trade in the validated record, newest first, with a running account ledger</caption>
      <thead><tr><th scope="col">#</th><th scope="col">Day</th><th scope="col">Entry</th><th scope="col">Exit</th><th scope="col">Net P&amp;L</th><th scope="col">Account</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
    <p class="tvt-note">Newest first &middot; Account is cumulative net from zero.</p>
  </div>"""

def calendar_real(tr):
    import datetime as _dt
    daily = tr["daily"]
    months = sorted({d[:7] for d in daily})[-6:]
    out = ""
    for ym in months:
        y, m = int(ym[:4]), int(ym[5:7])
        first = _dt.date(y, m, 1)
        start_off = first.weekday()  # Mon=0
        ndays = ((_dt.date(y + (m == 12), (m % 12) + 1, 1)) - first).days
        mon_lbl = first.strftime("%b %Y")
        cells = '<span class="rc-e"></span>' * start_off
        mtot = 0.0
        for day in range(1, ndays + 1):
            key = f"{ym}-{day:02d}"
            v = daily.get(key)
            if v is None:
                cells += f'<span class="rc-d"><i>{day}</i></span>'
            else:
                mtot += v
                cls = "rc-p" if v > 0 else ("rc-n" if v < 0 else "rc-d")
                val = f"{abs(v)/1000:.1f}k" if abs(v) >= 1000 else f"{abs(v):.0f}"
                sign = "" if v > 0 else "\u2212"
                cells += (f'<span class="rc-d {cls}" title="{day} {mon_lbl} &middot; {"+" if v > 0 else "-"}${abs(v):,.0f}">'
                          f'<i>{day}</i><b>{sign}{val}</b></span>')
        mname = first.strftime("%B %Y")
        tcls = "tv-pos" if mtot > 0 else ("tv-neg" if mtot < 0 else "")
        out += f"""<div class="rc-month">
      <div class="rc-h"><span>{mname}</span><b class="{tcls}">{'+' if mtot > 0 else ''}${mtot:,.0f}</b></div>
      <div class="rc-wd"><span>M</span><span>T</span><span>W</span><span>T</span><span>F</span><span>S</span><span>S</span></div>
      <div class="rc-g">{cells}</div>
    </div>"""
    return f"""<div class="record rcal">
  <div class="record-title">Daily results &mdash; last {len(months)} months of the record</div>
  <div class="rc-wrap">{out}</div>
</div>"""

def tester_block(p):
    b, f = p["best"]["stats"], (p.get("full") or {}).get("stats", {})
    slug = p["slug"]
    tr = load_trades_data(slug)
    if tr:
        lt_tab = f'<label for="tvt-{slug}-lt" class="tvt-tab tvt-tab-lt">Trade log</label>'
        lt_pane = trades_table(tr, slug)
    else:
        lt_tab = '<span class="tvt-tab tvt-tab-off" title="Activates when the trade-level export lands">Trade log &middot; soon</span>'
        lt_pane = ""
    tiles = ""
    for lab, key, cls in [("Net profit", "Net", "tv-pos"), ("Total trades", "Trades", ""),
                          ("Profitable", "Win", "tv-pos"), ("Profit factor", "PF", "tv-pos"),
                          ("Max drawdown", "Max DD", "tv-neg"), ("Avg trade", "$/trade", "tv-pos")]:
        v = b.get(key, "")
        tiles += f'<div class="tvt-tile"><span class="tvt-k">{lab}</span><b class="{cls}">{esc(v) or "&mdash;"}</b></div>'
    rows = ""
    for lab, key in TVT_ROWS:
        rows += (f'<tr><th scope="row">{lab}</th>{tvt_val(b, key, best=True)}{tvt_val(f, key)}</tr>')
    return f"""<div class="tvt" id="tester">
  <div class="tvt-bar">
    <span class="tvt-title">Strategy Tester &mdash; {esc(p['name'])}</span>
    <span class="tvt-src">validated run &middot; commissions + slippage modeled</span>
  </div>
  <input type="radio" name="tvt-{slug}" id="tvt-{slug}-ov" class="tvt-r" checked>
  <input type="radio" name="tvt-{slug}" id="tvt-{slug}-ps" class="tvt-r">
  <input type="radio" name="tvt-{slug}" id="tvt-{slug}-lt" class="tvt-r">
  <div class="tvt-tabs">
    <label for="tvt-{slug}-ov" class="tvt-tab tvt-tab-ov">Overview</label>
    <label for="tvt-{slug}-ps" class="tvt-tab tvt-tab-ps">Performance summary</label>
    {lt_tab}
  </div>
  <div class="tvt-pane tvt-ov">
    {chart_figure(p)}
    <div class="tvt-tiles">{tiles}</div>
    <p class="tvt-note">{f'Curve: the full record. Figures: best window &middot; {esc(p.get("window", ""))}.' if tr else f'Best window &middot; {esc(p.get("window", ""))}. Equity curve is illustrative, fitted to the published stats, until the trade-level export replaces it.'}</p>
  </div>
  <div class="tvt-pane tvt-ps">
    <div class="screener" tabindex="0" role="region" aria-label="Performance summary table, scrolls horizontally">
    <table class="tvt-table">
      <caption class="sr-only">Performance summary: best window vs full 2024+ window</caption>
      <thead><tr><th scope="col">Metric</th><th scope="col">Best window</th><th scope="col">Full record</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
  </div>
  {lt_pane}
</div>"""

def windows_block(p, label_prefix=""):
    b, f = p["best"], p["full"]
    out = f'''<div class="winset winset-best">
    <div class="win-h"><span class="win-tag win-tag-best">BEST WINDOW</span><span class="win-range">{esc(p.get("window",""))}</span></div>
    {tile_grid(b["stats"])}
  </div>'''
    if f:
        out += f'''
  <div class="winset">
    <div class="win-h"><span class="win-tag">FULL 2024+ WINDOW</span><span class="win-range">context</span></div>
    {tile_grid(f["stats"])}
  </div>'''
    return out

def engines_block(p):
    e = p["engines"]
    out = ""
    for key in sorted(e):
        d = e[key]
        label = d.get("label", key.upper())
        out += f'''<div class="winset winset-best">
    <div class="win-h"><span class="win-tag win-tag-eng">{label}</span><span class="win-range">{esc(d.get("window",""))}</span></div>
    {tile_grid(d["best"]["stats"])}
  </div>'''
        if d.get("full"):
            out += f'''
  <div class="winset">
    <div class="win-h"><span class="win-tag">FULL 2024+ WINDOW</span><span class="win-range">context</span></div>
    {tile_grid(d["full"]["stats"])}
  </div>'''
    return out

def _nice_step(span, target=4):
    import math as _m
    raw = span / max(1, target)
    mag = 10 ** _m.floor(_m.log10(raw)) if raw > 0 else 1
    for mult in (1, 2, 2.5, 5, 10):
        if raw <= mult * mag:
            return mult * mag
    return 10 * mag

def _fmt_usd(v):
    a = abs(v)
    s = "-" if v < 0 else ""
    if a >= 1000:
        return f"{s}${a/1000:,.0f}k" if a >= 10000 else f"{s}${a/1000:,.1f}k"
    return f"{s}${a:,.0f}"

def real_chart(p, tr):
    """TradingView-Strategy-Tester-style equity panel: time x-axis with date
    ticks, right-side $ scale, gridlines, equity area/line, and the running
    drawdown hanging below the zero baseline. Drawn from the real record."""
    from datetime import datetime as _dt
    eq = tr["equity"]                       # [(YYYY-MM-DD, cum), ...]
    ts = [_dt.strptime(d, "%Y-%m-%d") for d, _ in eq]
    ys = [v for _, v in eq]
    # running drawdown (<= 0) on the same $ scale — TV's lower red area
    dd = []
    peak = 0.0
    for v in ys:
        peak = max(peak, v)
        dd.append(v - peak)
    t0, t1 = ts[0], ts[-1]
    tspan = max(1.0, (t1 - t0).total_seconds())
    y_hi = max(max(ys), 0.0)
    y_lo = min(min(dd), 0.0)
    pad = 0.06 * (y_hi - y_lo or 1.0)
    y_hi += pad; y_lo -= pad

    # geometry (viewBox units; aspect preserved so text stays crisp)
    W, H = 720.0, 300.0
    L, R, T, B = 10.0, 62.0, 14.0, 30.0   # plot margins (right holds $ scale)
    PW, PH = W - L - R, H - T - B
    def X(t): return L + PW * ((t - t0).total_seconds() / tspan)
    def Y(v): return T + PH * (1 - (v - y_lo) / (y_hi - y_lo))

    eq_pts = " L".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in zip(ts, ys))
    dd_pts = " L".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in zip(ts, dd))
    y_zero = Y(0.0)
    eq_area = f"M{X(t0):.1f},{y_zero:.1f} L" + eq_pts + f" L{X(t1):.1f},{y_zero:.1f} Z"
    dd_area = f"M{X(t0):.1f},{y_zero:.1f} L" + dd_pts + f" L{X(t1):.1f},{y_zero:.1f} Z"

    # y gridlines at nice $ steps
    step = _nice_step(y_hi - y_lo)
    grid = ""
    v = step * int(y_lo // step)
    while v <= y_hi:
        if y_lo <= v <= y_hi:
            yy = Y(v)
            cls = "tvx-zero" if abs(v) < 1e-9 else "tvx-grid"
            grid += f'<line class="{cls}" x1="{L:.0f}" y1="{yy:.1f}" x2="{L+PW:.1f}" y2="{yy:.1f}"/>'
            grid += f'<text class="tvx-ylab" x="{L+PW+8:.1f}" y="{yy+3.5:.1f}">{_fmt_usd(v)}</text>'
        v += step

    # x ticks: ~6 evenly spaced dates; label style adapts to span
    months_span = (t1.year - t0.year) * 12 + (t1.month - t0.month)
    xticks = ""
    N = 6
    for i in range(N + 1):
        t = t0 + (t1 - t0) * i / N
        xx = X(t)
        lab = t.strftime("%b %y") if months_span >= 10 else t.strftime("%d %b")
        anchor = "start" if i == 0 else ("end" if i == N else "middle")
        xticks += f'<line class="tvx-grid tvx-vgrid" x1="{xx:.1f}" y1="{T:.0f}" x2="{xx:.1f}" y2="{T+PH:.1f}"/>'
        xticks += f'<text class="tvx-xlab" x="{xx:.1f}" y="{H-9:.1f}" text-anchor="{anchor}">{lab}</text>'

    net = p["best"]["stats"].get("Net", "")
    # the audited full-record Max DD, NOT a trough over the downsampled
    # equity array - sampling misses the exact bottom and understates risk
    dd_min = _fmt_usd(-abs(tr["full"]["dd"]))

    # CSS-only crosshair: one invisible hover strip per sampled point; each
    # reveals its own line + dot + label. ~110 points keeps pages light.
    hstep = max(1, len(ts) // 110)
    hidx = list(range(0, len(ts), hstep))
    if hidx[-1] != len(ts) - 1: hidx.append(len(ts) - 1)
    # ONE static readout box, top-left of the plot. Only the value text inside
    # it changes as the cursor moves, so nothing re-renders or repositions -
    # the vertical line and the tracing circle are the only moving parts.
    labels = [ts[i].strftime("%d %b %y") + " · " + ("-" if ys[i] < 0 else "") + "${:,.0f}".format(abs(ys[i]))
              for i in hidx]
    box_w = 7.0 * max(len(t) for t in labels) + 16
    box_x, box_y = L + 8, T + 6
    txt_x, txt_y = box_x + 8, box_y + 14.5
    hover = f'<rect class="hv-box" x="{box_x:.1f}" y="{box_y:.1f}" width="{box_w:.1f}" height="21" rx="3"/>'
    for pos, i in enumerate(hidx):
        x = X(ts[i]); y = Y(ys[i])
        x_prev = X(ts[hidx[pos-1]]) if pos > 0 else L
        x_next = X(ts[hidx[pos+1]]) if pos < len(hidx)-1 else L + PW
        x0 = (x_prev + x) / 2; x1 = (x + x_next) / 2
        hover += (f'<g class="hp"><rect class="hp-hit" x="{x0:.1f}" y="{T:.0f}" width="{max(0.5, x1-x0):.1f}" height="{PH:.1f}"/>'
                  f'<g class="hv"><line class="hv-line" x1="{x:.1f}" y1="{T:.0f}" x2="{x:.1f}" y2="{T+PH:.1f}"/>'
                  f'<circle class="hv-ring" cx="{x:.1f}" cy="{y:.1f}" r="6"/>'
                  f'<circle class="hv-dot" cx="{x:.1f}" cy="{y:.1f}" r="3.6"/>'
                  f'<text class="hv-txt" x="{txt_x:.1f}" y="{txt_y:.1f}">{labels[pos]}</text></g></g>')
    hover = f'<g class="hp-all">{hover}</g>'
    return f"""<figure class="chart-panel tvx">
    <div class="tvx-legend">
      <span class="tvx-key"><i class="tvx-dot tvx-dot-eq"></i>Equity <b>{_fmt_usd(ys[-1])}</b></span>
      <span class="tvx-key"><i class="tvx-dot tvx-dot-dd"></i>Drawdown <b class="tv-neg">{dd_min}</b></span>
      <span class="tvx-src">Full record &middot; {tr["full"]["n"]:,} closed trades &middot; {esc(tr["full"]["start"])} &rarr; {esc(tr["full"]["end"])}</span>
    </div>
    <svg viewBox="0 0 720 300" role="img" aria-label="Equity and drawdown, {tr['full']['n']} closed trades" focusable="false">
      <defs>
        <linearGradient id="tvxg-{p["slug"]}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#56C8A2" stop-opacity=".26"/>
          <stop offset="1" stop-color="#56C8A2" stop-opacity=".02"/>
        </linearGradient>
        <linearGradient id="tvxr-{p["slug"]}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stop-color="#E88585" stop-opacity=".04"/>
          <stop offset="1" stop-color="#E88585" stop-opacity=".30"/>
        </linearGradient>
      </defs>
      {grid}{xticks}
      <path class="tvx-ddarea" d="{dd_area}" fill="url(#tvxr-{p["slug"]})"/>
      <path class="tvx-ddline" d="M{dd_pts}" fill="none"/>
      <path class="tvx-eqarea" d="{eq_area}" fill="url(#tvxg-{p["slug"]})"/>
      <path class="tvx-eqline" d="M{eq_pts}" fill="none"/>
      {hover}
    </svg>
  </figure>"""

def chart_figure(p):
    tr = load_trades_data(p["slug"])
    if tr:
        return real_chart(p, tr)
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
    f = (p.get("full") or {}).get("stats", {})
    rodd, dd = num(b.get("RoDD", 0)), num(b.get("Max DD", 0))
    rodd_full = num(f.get("RoDD", 0))
    dd_full = num(f.get("Max DD", 0))
    months = num(b.get("Months", 0))
    net = b.get("Net", "")
    if not rodd or not dd: return ""
    # the guard trips on the WORSE window, never the flattering one: sizing to a
    # best-window drawdown is how a buyer gets wiped by the full record
    red_at = max(dd, dd_full)
    guard_src = "full record" if dd_full > dd else "this window"
    if p["slug"] == "pool-milestone-pullback":
        red_at = max(red_at, 12300)  # unfilterable worst session — sizing guard
    slug = p["slug"]
    radios, labels, outs = "", "", ""
    default_set = False
    for i, C in enumerate(NOTCHES, 1):
        if C < red_at: state = "red"
        elif C < 2 * red_at: state = "amb"
        else: state = "ok"
        checked, rec = "", False
        if state == "ok" and not default_set:
            checked = " checked"; default_set = True; rec = True
        proj = rodd * C
        permo = proj / months if months else 0
        lab = f"${C//1000}k" if C >= 1000 and C % 1000 == 0 else f"${C/1000:.1f}k"
        radios += f'<input type="radio" name="ro-{slug}" id="ro-{slug}-{i}" class="ro-r ro-{state}"{checked}>'
        rec_tag = '<span class="ro-rec">OUR PICK</span>' if rec else ''
        labels += (f'<label for="ro-{slug}-{i}" class="ro-notch{" ro-notch-rec" if rec else ""}">{rec_tag}<span class="ro-tick" aria-hidden="true"></span>'
                   f'<span class="ro-amt">{lab}</span></label>')
        if state == "red":
            body = (f'<span class="ro-flag">NOT BUILT FOR THIS SIZE</span> The deepest published max drawdown '
                    f'({usd(red_at)}, {guard_src}) exceeds a {lab} budget &mdash; this sizing would not have '
                    f'survived the sample. Some systems are not meant to run this small.')
        else:
            proj_full = rodd_full * C
            both = (f' Over the full record, <b>{usd(proj_full)}</b>.' if rodd_full and abs(rodd_full - rodd) > 0.01 else '')
            body = (f'A drawdown budget of <b>{lab}</b> historically returned <b class="ro-ret">~{usd(proj)}</b> '
                    f'over the best window.{both} Past results, not a forecast.')
            if rec:
                body = ('<span class="ro-flag ro-flag-rec">RECOMMENDED SIZE</span> The smallest budget that clears '
                        f'the deepest published drawdown ({usd(red_at)}, {guard_src}). ' + body)
            if state == "amb":
                body = (f'<span class="ro-flag">THIN CUSHION</span> The deepest published drawdown ({usd(red_at)}, '
                        f'{guard_src}) is more than half this budget &mdash; one bad stretch uses most of your '
                        'room. ' + body)
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
THEMED = {p["slug"] for p in sorted(CAT["strategies"], key=lambda x: -x["price"])[:6]}
THEMED |= {b["slug"] for b in CAT["books"]}

os.makedirs(os.path.join(BASE, "strategies"), exist_ok=True)
urls = ["/", "/plan.html", "/terms.html", "/privacy.html"]

def product_page(p, is_book):
    path = f"/strategies/{p['slug']}.html"
    urls.append(path)
    b = p["best"]["stats"]
    mdesc = (f"{p['name']} ({p['actual']}): RoDD {b.get('RoDD','')} on the published window, "
             f"PF {b.get('PF','')}, {b.get('Trades','')} trades. Live-validated. "
             f"TradingView invite-only script, activated within 24h.")
    crumb_root = ('<a href="/strategies/the-books.html">The Books</a>' if is_book
                  else '<a href="/#strategies">Strategies</a>')
    _tr = load_trades_data(p["slug"])
    main_col = rodd_menu(p) + "\n" + tester_block(p) + "\n" + (
        engines_block(p) if p.get("engines") else "")
    main_col += "\n" + warn_block(p) + "\n" + legs_block(p)
    # the calendar wants the whole page width, not the narrow main column
    cal_col = calendar_real(_tr) if _tr else calendar_panel()
    xsell = None
    struck = None
    if is_book:
        others = [bk for bk in CAT["books"] if bk["slug"] != p["slug"]]
        xsell = ('All four engines: <a href="/strategies/the-books.html">The Books — $2,999/mo</a> · '
                 + " · ".join(f'<a href="/strategies/{o["slug"]}.html">{esc(o["name"])}</a>' for o in others[:2]))
    page = head(f"{p['name']} — FuturesTradingBots", mdesc, path,
                bodycls=(f"pdp-theme fc-{p['slug']}" if p["slug"] in THEMED else ""))
    page += f"""
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb">{crumb_root}<span class="sep">/</span>{esc(p['name'])}</nav>

    <article class="pdp">
      <div class="pdp-head">
        {('<span class="pdp-glyph" aria-hidden="true">' + (emblem(p['slug'], 'bk-emblem pdp-mark') if is_book else glyph(p['slug'], 'glyph pdp-mark')) + '</span>') if p['slug'] in THEMED else ''}
        <div class="pdp-id">
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
        <div class="pdp-side">
        {buybox(p['name'], f"{p['price']:,}", p['name'] + " / " + p['actual'], xsell=xsell, href=buy_href(p))}
        {sep_block(p)}
        </div>
      </div>

      <div class="pdp-wide">{cal_col}</div>

      <div class="pdp-disclaim">
        <p class="disclaim-sm">{esc(DISCLAIMER)}</p>
      </div>

      <a class="backlink" href="{'/strategies/the-books.html' if is_book else '/#strategies'}">&larr; {'The Books' if is_book else 'All strategies'}</a>
    </article>
  </div>
"""
    page += FOOTER
    open(os.path.join(BASE, "strategies", p["slug"] + ".html"), "w", encoding="utf-8").write(page)

if not PRELAUNCH:
    for p in CAT["strategies"]:
        product_page(p, is_book=False)
    for p in CAT["books"]:
        product_page(p, is_book=True)

# ── bundle pages ────────────────────────────────────────────────
BN = CAT["bundles"]

def bundle_page(slug, name, price, struck, desc, extra, xsell):
    path = f"/strategies/{slug}.html"
    urls.append(path)
    page = head(f"{name} — FuturesTradingBots", desc + " TradingView invite-only scripts, activated within 24h.", path)
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
        {buybox(name, f"{price:,}", name + " bundle", xsell=xsell, struck=f"{struck:,}" if struck else None, href=WHOP_STORE)}
      </div>
      <div class="pdp-disclaim"><p class="disclaim-sm">{esc(DISCLAIMER)}</p></div>
      <a class="backlink" href="/#packages">&larr; Bundles</a>
    </article>
  </div>
"""
    page += FOOTER
    open(os.path.join(BASE, "strategies", slug + ".html"), "w", encoding="utf-8").write(page)

_prices = sorted((s["price"] for s in CAT["strategies"]), reverse=True)
COMBINED_ALL = sum(_prices)
COMBINED_TOP3 = sum(_prices[:3])

inc_rows = "".join(
    f'<li><a class="sys-link" href="/strategies/{s["slug"]}.html"><span class="inc-name">{esc(s["name"])}</span></a>'
    f'<span class="inc-price">${s["price"]}/mo</span></li>'
    for s in sorted(CAT["strategies"], key=lambda x: -x["price"]))
if not PRELAUNCH and HAS_BUNDLES:
    bundle_page("all-access", "All-Access", BN["all_access"]["price"], COMBINED_ALL,
        "Every validated strategy in the catalog. The Books are not included.",
        f"""<div class="record">
            <div class="record-title">Included — all {len(CAT["strategies"])} validated systems (combined ${COMBINED_ALL:,}/mo)</div>
            <div class="included included-scroll" tabindex="0" role="region" aria-label="All included systems"><ul>{inc_rows}</ul></div>
            <p class="record-note">{"The Books are not included in All-Access. The four in-house engines are a separate premium tier." if HAS_BOOKS_BUNDLE else "The in-house Books are still in validation; when they publish they will be a separate tier, not part of All-Access."}</p>
          </div>""",
        ('Want the engines themselves? <a href="/strategies/the-books.html">The Books — $2,999/mo</a>'
         if HAS_BOOKS_BUNDLE else
         'Not ready for everything? Subscribe to the systems you want one at a time.'))

    # Pick-3 retired: the plan finder recommends three solo subscriptions instead

if not PRELAUNCH and HAS_BOOKS_BUNDLE:
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

if not PRELAUNCH and HAS_STARTER:
    ST = BN["starter"]
    by_slug = {s["slug"]: s for s in CAT["strategies"]}
    starter_rows = "".join(
        f'<li><a class="sys-link" href="/strategies/{s}.html"><span class="inc-name">{esc(by_slug[s]["name"])}</span></a>'
        f'<span class="inc-price">{esc(by_slug[s]["actual"])} · ${by_slug[s]["price"]}/mo solo</span></li>'
        for s in ST["slugs"])
    starter_names = " + ".join(by_slug[s]["name"] for s in ST["slugs"])
    bundle_page("the-starter", "The Starter", ST["price"], ST["combined"],
        "Three low-drawdown, high-win-rate session systems. The safest door into the catalog.",
        f"""<div class="record">
            <div class="record-title">Included — three low-drawdown session systems</div>
            <ul class="included">{starter_rows}</ul>
            <p class="record-note">{starter_names}: the three smallest published drawdowns in the value tiers, every one winning over 77% of its trades on the published window. Worth ${ST["combined"]}/mo solo.</p>
          </div>""",
        'Outgrow it? <a href="/strategies/all-access.html">All-Access — $999/mo</a>')

# ── success page ────────────────────────────────────────────────
if True:
    psucc = head("Order Confirmed — FuturesTradingBots",
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
              <!-- DISCORD: community invite --><a class="btn btn-discord" href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener">Ask in Discord</a>
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
    p404 = head("404 — FuturesTradingBots", "Page not found.", "/404.html").replace(
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
            <a class="btn btn-solid" href="/">Back to home</a>
            <a class="btn" href="/#strategies">Browse strategies</a>
          </div>
        </div>
      </div>
    """
    p404 += FOOTER
    open(os.path.join(BASE, "404.html"), "w", encoding="utf-8").write(p404)


    # ── legal pages ─────────────────────────────────────────────────


def legal_toc(body):
    """Build a section index from the body's own numbered h2s, and stamp
    matching ids on them so the links resolve."""
    secs = re.findall(r'<h2><span class="n">(\d+)</span>\s*(.*?)</h2>', body, re.S)
    if not secs:
        return body, ""
    for n, _t in secs:
        body = body.replace(f'<h2><span class="n">{n}</span>',
                            f'<h2 id="s{n}"><span class="n">{n}</span>', 1)
    items = "".join(
        f'<li><a href="#s{n}"><span class="toc-n">{n}</span>'
        f'<span class="toc-t">{re.sub(r"<[^>]+>", "", t).strip()}</span></a></li>'
        for n, t in secs)
    toc = f'<nav class="legal-toc" aria-label="Sections"><span class="toc-h">Sections</span><ol>{items}</ol></nav>'
    return body, toc

def legal_page(fname, title, body):
    page = head(f"{title} — FuturesTradingBots",
                f"{title} for FuturesTradingBots — TradingView invite-only strategy subscriptions sold through Whop.",
                f"/{fname}")
    body, toc = legal_toc(body)
    page += f"""
  <div class="wrap legal-wrap">
    {toc}
    <div class="legal">
    {body}
    </div>
  </div>
"""
    page += FOOTER
    open(os.path.join(BASE, fname), "w", encoding="utf-8").write(page)

TERMS_BODY = """<h1>Terms of Service</h1>
<p class="updated">Last updated: 21 August 2026</p>

<h2><span class="n">01</span> Who we are, and what these terms cover</h2>
<p>FuturesTradingBots (&ldquo;we&rdquo;, &ldquo;us&rdquo;) publishes trading-strategy software delivered as
invite-only TradingView scripts. By purchasing a subscription or using this site you agree to these
terms. If you do not agree, do not purchase access.</p>

<h2><span class="n">02</span> What you are buying</h2>
<p>A subscription is a <strong>license to use software</strong> &mdash; access to one or more strategy
scripts on the TradingView platform for as long as your subscription is active. It is not a managed
account, not a trading service, not a signal service operated on your behalf, and not financial,
investment, legal, or tax advice. We are software publishers, not advisers or brokers, and no
fiduciary relationship is created.</p>

<h2><span class="n">03</span> Billing, cancellation, refunds &mdash; and our two guarantees</h2>
<p>All payments are processed by Whop; we never see or store your payment details. Subscriptions renew
automatically until cancelled. You can cancel anytime through Whop and access runs to the end of the
paid period, then revokes automatically. All refunds are issued through Whop.</p>
<p><strong>1. Seven-day money-back.</strong> Within 7 days of your first charge for a product, request a
refund and you get it in full &mdash; no questions, no conditions. One per customer per product; applies
to the first purchase, not renewals.</p>
<p><strong>2. First-month performance guarantee.</strong> If a strategy&rsquo;s own published signals net
a loss over your first 30 days of access &mdash; measured on the strategy&rsquo;s official signal record
at the position size that record was produced at, with commissions and slippage modeled &mdash; the same accounting used for every figure
on this site &mdash; you get a full refund of your first month on request. Request within 7 days after
your first 30 days end; one per customer per product. The measure is the strategy&rsquo;s signal record,
not any individual account&rsquo;s fills, sizing, or discretionary deviations &mdash; that keeps the test
objective and checkable by both of us.</p>
<p><strong>Referrals.</strong> Referral links give the buyer 10% off at checkout and pay the referrer a
recurring commission through Whop&rsquo;s affiliate system at the rate shown in their Whop affiliate
dashboard (currently 15% for founding members; rates for later-joining affiliates may differ, and
existing referral relationships keep the rate they were earned under). Referral rewards may be withheld
where self-referral or abuse is evident. Billing disputes should be raised through Whop first so they
reach us fastest.</p>

<h2><span class="n">04</span> Access and your TradingView username</h2>
<p>Delivery requires a valid TradingView username, which you provide at checkout. We grant invite-only
access to that username, normally within 24 hours of purchase. Keeping the username accurate is your
responsibility; access is revoked automatically when a subscription lapses or is refunded.</p>

<h2><span class="n">05</span> Acceptable use</h2>
<ul>
<li>One subscription covers one TradingView account. Do not share, pool, or resell access.</li>
<li>Do not copy, decompile, reverse-engineer, republish, or redistribute any script, its source, its
settings, or its signals, in whole or in part.</li>
<li>Do not misrepresent our published statistics or use our name or materials to market a third-party
product.</li>
</ul>
<p>We may suspend or revoke access for violations, without refund where the law allows.</p>

<h2><span class="n">06</span> Performance figures</h2>
<p>Every statistic on this site comes from backtested or validation runs over the stated windows, with
commissions and slippage modeled, published exactly as the run produced them. Backtested and
hypothetical performance has inherent limitations, does not represent live trading, and is not a
guarantee or projection of future results. You can lose money, including more than you deposit,
trading futures. Only risk capital should be used. The full risk and hypothetical-performance
disclosures in the footer of every page form part of these terms.</p>

<h2><span class="n">07</span> Intellectual property</h2>
<p>All scripts, code, names, marks, statistics, and site content remain our property. Your
subscription grants a limited, non-exclusive, non-transferable, revocable license to use the scripts
for your own trading while the subscription is active. No other rights are granted.</p>

<h2><span class="n">08</span> Disclaimer of warranties; limitation of liability</h2>
<p>The scripts and this site are provided <strong>as is</strong>, without warranties of any kind,
express or implied, including merchantability, fitness for a particular purpose, and uninterrupted or
error-free operation. TradingView and Whop are independent platforms we do not control. To the maximum
extent permitted by law, our total liability for any claim arising out of these terms or your use of
the software is limited to the subscription fees you paid us in the three months before the claim
arose; we are not liable for trading losses, lost profits, or indirect, incidental, or consequential
damages.</p>

<h2><span class="n">09</span> Changes, termination, governing law</h2>
<p>We may update these terms; the &ldquo;last updated&rdquo; date changes when we do, and continued use
after a change is acceptance. We may discontinue a product at any time; if we discontinue something
you have paid for, the unused portion is refunded through Whop. These terms are governed by the laws
of the United States and of the state in which FuturesTradingBots is organized, without regard to
conflict-of-law rules.</p>
<!-- LEGAL: set the specific state of organization here once the entity is formed -->

<h2><span class="n">10</span> Contact</h2>
<p>Questions about these terms: ask in our <!-- DISCORD: community invite --><a href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener">Discord</a>, where support runs.</p>"""

PRIVACY_BODY = """<h1>Privacy Policy</h1>
<p class="updated">Last updated: 21 August 2026</p>

<h2><span class="n">01</span> The short version</h2>
<p>This site is a static page. It has no accounts, no login, no forms, no cookies, no analytics, no
trackers, and it runs no scripts in your browser. We cannot collect what never exists: browsing this
site sends us nothing about you.</p>

<h2><span class="n">02</span> What we never collect</h2>
<ul>
<li>No cookies or local storage, first- or third-party.</li>
<li>No analytics, pixels, fingerprinting, or session recording.</li>
<li>No account data &mdash; there are no accounts on this site.</li>
<li>No payment details &mdash; we never see or store card numbers.</li>
</ul>

<h2><span class="n">03</span> What third parties process</h2>
<ul>
<li><strong>Whop</strong> runs checkout and billing. When you buy, Whop collects your name, email,
payment details, and your TradingView username under
<a href="https://whop.com/privacy" rel="noopener">Whop&rsquo;s privacy policy</a>. Whop shares with us
only what we need to deliver access: your order, email, and TradingView username.</li>
<li><strong>TradingView</strong> hosts the strategy scripts. Granting invite-only access associates
your TradingView username with our scripts under TradingView&rsquo;s own policies.</li>
<li><strong>GitHub Pages and Cloudflare</strong> serve this site and keep standard, short-lived server
logs (IP address, user agent, requested page) for security and delivery, under their own policies. We
do not receive or mine those logs.</li>
<li><strong>Google Fonts</strong> serves the site&rsquo;s typefaces; your browser requests font files
from Google&rsquo;s servers, which sees the request metadata (IP, user agent).</li>
<li><strong>Discord</strong> hosts our community; joining it is optional and governed by
Discord&rsquo;s terms and privacy policy.</li>
</ul>

<h2><span class="n">04</span> What we do with what we have</h2>
<p>The data we hold is your order record, your email, and your TradingView username. We use them for
exactly three things: granting and revoking script access, support, and service messages about your
subscription. We do not sell data, run marketing lists, or share anything beyond the processors named
above.</p>

<h2><span class="n">05</span> Email support</h2>
<p>If you email support, we keep the thread to help you and for our records. Nothing else is done
with it.</p>

<h2><span class="n">06</span> Retention and your rights</h2>
<p>Order records are kept as long as bookkeeping and tax rules require; access records are kept while
your subscription is active. Email us to ask what we hold about you, to correct it, or to request
deletion of anything we are not legally required to keep.</p>

<h2><span class="n">07</span> Children</h2>
<p>This site and our products are not directed at anyone under 18, and futures trading is not either.</p>

<h2><span class="n">08</span> Changes and contact</h2>
<p>If this policy changes, the date above changes with it. Questions: ask in our <!-- DISCORD: community invite --><a href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener">Discord</a>.</p>"""

legal_page("terms.html", "Terms of Service", TERMS_BODY)
legal_page("privacy.html", "Privacy Policy", PRIVACY_BODY)

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
