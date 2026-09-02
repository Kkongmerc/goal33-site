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
WHOP_STORE = CAT.get("whop_store") or "/"
PROMO = CAT.get("promo") or {}
PROMO_LINE = PROMO.get("line", "").replace("{code}", PROMO.get("code", "")) if PROMO else ""
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

def pct(v):
    """RoDD-style ratios sell as percentages: 11.06x -> 1,106%."""
    return "{:,.0f}%".format(num(v) * 100)

def rodd_mo_pct(stats):
    """Average monthly return on drawdown, as a percentage, computed fresh
    from RoDD / Months -- never the stored RoDD/mo field, which can drift
    out of sync with RoDD after a data refresh (owner ruling 2026-09-02)."""
    rodd, months = num(stats.get("RoDD", 0)), num(stats.get("Months", 0))
    return "{:,.0f}%".format(rodd / months * 100) if months else "—"

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
<meta name="theme-color" content="#131722">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:site_name" content="FuturesTradingBots">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}{path}">
<link rel="canonical" href="{SITE}{path}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600;700&family=Fragment+Mono&display=swap">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/main.css?v={CSSV}">
</head>
<body{f' class="{bodycls}"' if bodycls else ''}>
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
    <a class="btn btn-sm btn-buy" href="{WHOP_STORE}" rel="noopener">Get access</a>
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

<main id="main">
"""

FOOTER = f"""</main>

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
  <div class="price">{was}<span class="now">${price}</span><span class="per">/mo</span></div>
  <span class="annual">Annual = 2 months free</span>
  <!-- WHOP: checkout ({whop_note}) -->
  <a class="btn btn-buy" href="{href}" rel="noopener">Get access</a>
  <p class="buy-promo">{esc(PROMO_LINE)}</p>
  <div class="guar">
    <span class="guar-line"><b>7-day</b> money-back &mdash; no questions</span>
    <span class="guar-line"><b>60-day</b> Performs-as-Published guarantee</span>
    <span class="guar-note">strategy matches its published signals &middot; claim within 60 days &middot; <a href="/terms.html">terms</a></span>
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
ORDER = ["RoDD", "RoDD/mo", "PF", "Win", "Net", "Max DD", "Risk/trade", "Max loss", "Return on risk/mo", "Trades", "$/trade", "Months"]

def tile_grid(stats):
    cells = ""
    for k in ORDER:
        if k in stats:
            hot = ' hot' if is_hot(k, stats[k]) else ''
            if k == "Max DD":
                n = num(stats[k])
                hot += ' dd-gold' if n <= 2000 else (' dd-neon' if n <= 5000 else '')
            if k == "RoDD":
                shown = pct(stats[k])
            elif k == "RoDD/mo":
                shown = rodd_mo_pct(stats)
            else:
                shown = esc(stats[k])
            cells += f'<div class="wtile{hot}"><span class="wk">{esc(k)}</span><span class="wv">{shown}</span></div>'
    for k, v in stats.items():
        if k not in ORDER:
            cells += f'<div class="wtile"><span class="wk">{esc(k)}</span><span class="wv">{esc(v)}</span></div>'
    return f'<div class="wtiles">{cells}</div>'

TVT_ROWS = [("Net profit", "Net"), ("Total closed trades", "Trades"), ("Percent profitable", "Win"),
            ("Profit factor", "PF"), ("Max drawdown", "Max DD"), ("Avg per trade", "$/trade"),
            ("Return on max drawdown", "RoDD"), ("RoDD per month", "RoDD/mo"),
            ("Risk per trade (median loss)", "Risk/trade"), ("Max loss (single trade)", "Max loss"),
            ("Return on risk per month", "Return on risk/mo"), ("Months in window", "Months")]

def tvt_val(stats, key, best=False):
    v = stats.get(key, "")
    if v in ("", None): return '<td class="tv-mut">&mdash;</td>'
    cls = "tv-pos" if key in ("Net", "PF", "Win", "RoDD", "RoDD/mo", "$/trade", "Return on risk/mo") else ("tv-neg" if key in ("Max DD", "Risk/trade", "Max loss") else "")
    if key == "Max DD" and best:
        n2 = num(v)
        cls += " dd-gold" if n2 <= 2000 else (" dd-neon" if n2 <= 5000 else "")
    if key == "RoDD":
        disp = pct(v)
    elif key == "RoDD/mo":
        disp = rodd_mo_pct(stats)
    else:
        disp = esc(v)
    return f'<td class="{cls}">{disp}</td>'

HELD_FULL = {
    "< 10m": "held less than 10 minutes", "< 30m": "held less than 30 minutes",
    "< 1h": "held less than an hour", "1-2h": "held approx. 1-2 hours",
    "2-4h": "held approx. 2-4 hours", "4-12h": "held approx. 4-12 hours",
    "12h+": "held over 12 hours",
}

LOG_ROW_CAP = 600  # most recent closed trades rendered; DOM/page-weight budget (midas at full
                   # depth shipped a 497KB / ~46k-node table). Stats, equity and calendar always
                   # cover the whole record - only the granular log is depth-capped.

def trades_table(tr, slug):
    """Entries, exits, the trade's net, and a running account ledger.
    The ledger is cumulative net from zero - the record carries no opening
    balance, so starting anywhere else would be inventing a number. The ledger
    accumulates over the WHOLE record even when only the newest LOG_ROW_CAP
    rows render, so the Account column always matches the published totals."""
    rows = ""
    n = len(tr["trades"])
    # walk forward to accumulate, then render newest-first
    running, ledger = 0.0, []
    for r in tr["trades"]:
        running += r[3]
        ledger.append(running)
    first_shown = max(0, n - LOG_ROW_CAP)
    for i in range(n - 1, first_shown - 1, -1):
        r = list(tr["trades"][i]) + [None] * 4
        day, epx, xpx, pnl, side = r[0], r[1], r[2], r[3], r[4]
        cls = "tv-pos" if pnl > 0 else ("tv-neg" if pnl < 0 else "")
        acc = ledger[i]
        acls = "tv-pos" if acc > 0 else ("tv-neg" if acc < 0 else "")
        side_td = ('<td class="lt-side lt-long">Long</td>' if side == "L" else
                   ('<td class="lt-side lt-short">Short</td>' if side == "S" else '<td class="lt-side">&mdash;</td>'))
        rows += (f'<tr><td>{i + 1}</td><td>{esc(day)}</td>{side_td}'
                 f'<td>{epx if epx is not None else "&mdash;"}</td>'
                 f'<td>{xpx if xpx is not None else "&mdash;"}</td>'
                 f'<td class="{cls}">{_tv_money(pnl)}</td>'
                 f'<td class="lt-acc {acls}">{_tv_money(acc)}</td></tr>')
    shown = n - first_shown
    if shown < n:
        span_note = (f'Most recent {shown:,} of {n:,} closed trades (from '
                     f'{esc(tr["trades"][first_shown][0])}) &middot; every stat, the equity curve and the '
                     f'calendar cover the full record')
        caption = (f'Most recent {shown:,} closed trades of the validated record, newest first, '
                   f'with a running account ledger over the full record')
    else:
        span_note = 'Every closed trade in the validated record'
        caption = 'Every closed trade in the validated record, newest first, with a running account ledger'
    return f"""<div class="tvt-pane tvt-lt">
    <div class="screener lt-scroll" tabindex="0" role="region" aria-label="Trade log, scrolls">
    <table class="tvt-table lt-table">
      <caption class="sr-only">{caption}</caption>
      <thead><tr><th scope="col">Trade #</th><th scope="col">Date</th><th scope="col">Side</th><th scope="col">Entry price</th><th scope="col">Exit price</th><th scope="col">Profit</th><th scope="col">Cumulative profit</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    </div>
    <p class="tvt-note">{span_note} &middot; Newest first &middot; Account is cumulative net from zero.</p>
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

def _tv_money(v, signed=False):
    """TradingView money form: -$97.50, +$9,942.50 (signed), $600.00."""
    a = abs(v)
    s = "-" if v < 0 else ("+" if signed and v > 0 else "")
    return f"{s}${a:,.2f}"

INITIAL_CAPITAL = 25000.0   # the "25 K USD" the report is stated against (owner's TV report, 2026-09-03)
COMMISSION_RT = 1.50        # USD per contract, round turn (micros, owners' standing cost basis)
MINUS = "−"

def _tvr_usd(v, signed=False):
    """TV report money: '9,421.50 USD', '−889.50 USD', '+9,421.50 USD' when signed."""
    a = abs(v)
    s = MINUS if v < 0 else ("+" if signed and v > 0 else "")
    return f"{s}{a:,.2f} USD"

def _tvr_pct(v, signed=False, dp=2):
    s = MINUS if v < 0 else ("+" if signed and v > 0 else "")
    return f"{s}{abs(v):.{dp}f}%"

def _sgn(v):
    return "tv-pos" if v > 0 else ("tv-neg" if v < 0 else "")

def _rows_of(tr):
    """Every closed trade as a dict; older 4-column records get null side/signal/qty/return."""
    import datetime as _dt
    out = []
    for r in tr["trades"]:
        r = list(r) + [None] * (8 - len(r))
        try:
            d = _dt.datetime.strptime(r[0], "%d %b %y").date()
        except Exception:
            continue
        out.append({"d": d, "epx": r[1], "xpx": r[2], "pnl": float(r[3]), "side": r[4],
                    "sig": r[5], "qty": r[6], "ret": r[7]})
    return out

def _window_rows(tr, which):
    """The record's rows inside its own <which> window. The slice must reproduce the
    published n and net, or the whole record is used and labelled as such."""
    import datetime as _dt
    w = tr[which]
    s, e = _dt.date.fromisoformat(w["start"]), _dt.date.fromisoformat(w["end"])
    rows = [r for r in _rows_of(tr) if s <= r["d"] <= e]
    if len(rows) != w["n"] or abs(sum(r["pnl"] for r in rows) - w["net"]) > 1:
        return _rows_of(tr), False
    return rows, True

def _agg(rows):
    """TradingView's Performance-Summary numbers for a set of trades."""
    pnls = [r["pnl"] for r in rows]
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x < 0]
    gp, gl = sum(wins), -sum(losses)
    n = len(pnls)
    cum = peak = dd = 0.0
    for x in pnls:
        cum += x
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    rets = [r["ret"] for r in rows if r["ret"] is not None]
    comm = [float(r["qty"]) * COMMISSION_RT for r in rows if r["qty"] is not None]
    return {
        "n": n, "wins": len(wins), "losses": len(losses), "be": n - len(wins) - len(losses),
        "net": sum(pnls), "gp": gp, "gl": gl, "pf": (gp / gl) if gl else 0.0, "dd": dd,
        "aw": gp / len(wins) if wins else 0.0, "al": -gl / len(losses) if losses else 0.0,
        "lw": max(wins) if wins else 0.0, "ll": min(losses) if losses else 0.0,
        "avg": sum(pnls) / n if n else 0.0, "winrate": 100.0 * len(wins) / n if n else 0.0,
        "avg_ret": sum(rets) / len(rets) if rets else None,
        "commission": sum(comm) if comm and len(comm) == n else None,
    }

def window_trade_stats(tr, which):
    """Derived rows for the details table, sliced by the record's own window
    boundaries. Returns None unless the slice reproduces the published n and net."""
    rows, exact = _window_rows(tr, which)
    if not exact:
        return None
    a = _agg(rows)
    a["ratio"] = (a["aw"] / abs(a["al"])) if a["al"] else 0.0
    return a

def _ta_row(lab, bv, fv, cls=""):
    return (f'<tr><th scope="row">{lab}</th>'
            f'<td class="{cls}">{bv}</td><td class="{cls}">{fv}</td></tr>')

def _cell(label, value, vcls="", sub="", subcls="", title=""):
    t = f' title="{esc(title)}"' if title else ""
    sub_html = f'<i class="{subcls}">{sub}</i>' if sub else ""
    return (f'<div class="tvr-cell"{t}><span class="tvr-k">{label}</span>'
            f'<span class="tvr-v"><b class="{vcls}">{value}</b>{sub_html}</span></div>')

def _pill_tabs(name, slug, items, checked=0):
    """CSS-radio pill row. items: (key, label, live). Returns (inputs, nav)."""
    inputs, labs = "", ""
    live_i = 0
    for key, lab, live in items:
        if live:
            iid = f"tvr-{slug}-{name}-{key}"
            inputs += f'<input type="radio" name="tvr-{slug}-{name}" id="{iid}" class="tvt-r"{" checked" if live_i == checked else ""}>'
            labs += f'<label for="{iid}" class="tvr-pill">{lab}</label>'
            live_i += 1
        else:
            labs += f'<span class="tvr-pill tvr-pill-off" title="Not part of the published record">{lab}</span>'
    return inputs, f'<nav class="tvr-pills">{labs}</nav>'

def _tvr_date(d):
    return d.strftime("%b %d, %Y").replace(" 0", " ")

# ── the Performance chart (TV's new report: cumulative PnL line, per-trade bars, day strip) ──
def real_chart(p, tr):
    from datetime import datetime as _dt, date as _date, timedelta as _td
    eq = tr["equity"]                       # [(YYYY-MM-DD, cum), ...]
    ts = [_dt.strptime(d, "%Y-%m-%d") for d, _ in eq]
    ys = [v for _, v in eq]
    rows = _rows_of(tr)
    t0, t1 = ts[0], ts[-1]
    tspan = max(1.0, (t1 - t0).total_seconds())
    W, H = 560.0, 300.0
    L, R, T, B = 4.0, 72.0, 14.0, 40.0
    PW, PH = W - L - R, H - T - B
    y_hi = max(max(ys), 0.0); y_lo = min(min(ys), 0.0)
    step = _nice_step(y_hi - y_lo, 5)
    y_hi = step * (int(y_hi // step) + 1)
    y_lo = step * int(y_lo // step) if y_lo < 0 else 0.0
    LINE_H = PH * 0.70                      # the line lives in the upper band
    def X(t): return L + PW * ((t - t0).total_seconds() / tspan)
    def Y(v): return T + LINE_H * (1 - (v - y_lo) / (y_hi - y_lo))
    eq_pts = " L".join(f"{X(t):.1f},{Y(v):.1f}" for t, v in zip(ts, ys))
    grid = ""
    v = y_lo
    while v <= y_hi + 1e-9:
        yy = Y(v)
        grid += f'<line class="tvr-grid" x1="{L:.0f}" y1="{yy:.1f}" x2="{L+PW:.1f}" y2="{yy:.1f}"/>'
        grid += f'<text class="tvr-ylab" x="{L+PW+6:.1f}" y="{yy+3.5:.1f}">{v:,.2f}</text>'
        v += step
    # per-trade bars in the lower band (daily net when the record is long)
    base_y = T + PH * 0.86
    amp = PH * 0.13
    if len(rows) <= 800:
        bars_src = [(_dt(r["d"].year, r["d"].month, r["d"].day), r["pnl"]) for r in rows]
        bars_lab = "Trades"
    else:
        bars_src = [(_dt.strptime(d, "%Y-%m-%d"), v) for d, v in sorted(tr["daily"].items())]
        bars_lab = "Trading days"
    bmax = max(abs(v) for _, v in bars_src) or 1.0
    bw = max(0.8, min(3.0, PW / max(1, len(bars_src)) * 0.8))
    bars = ""
    for t, v in bars_src:
        h = amp * abs(v) / bmax
        x = X(t) - bw / 2
        if v >= 0:
            bars += f'<rect class="tvr-bu" x="{x:.1f}" y="{base_y-h:.1f}" width="{bw:.1f}" height="{max(h,0.6):.1f}"/>'
        else:
            bars += f'<rect class="tvr-bd" x="{x:.1f}" y="{base_y:.1f}" width="{bw:.1f}" height="{max(h,0.6):.1f}"/>'
    bars += f'<line class="tvr-grid" x1="{L:.0f}" y1="{base_y:.1f}" x2="{L+PW:.1f}" y2="{base_y:.1f}"/>'
    # day-result strip under the plot
    days = sorted(tr["daily"].items())
    sw = max(1.0, PW / max(1, (t1 - t0).days + 1))
    strip_y = T + PH + 4
    strip = "".join(
        f'<rect class="{"tvr-du" if v > 0 else ("tvr-dd" if v < 0 else "tvr-dz")}" x="{X(_dt.strptime(d, "%Y-%m-%d")) - sw/2:.1f}" y="{strip_y:.0f}" width="{sw:.1f}" height="4"/>'
        for d, v in days)
    # x-axis: TV's style - month names at month changes, day numbers between
    ndays = max(1, (t1 - t0).days)
    stepd = next(s for s in (2, 3, 5, 7, 10, 14, 21, 30, 45, 60, 90) if ndays / s <= 13)
    xt = ""
    prev_m = None
    d = t0
    while d <= t1:
        lab = d.strftime("%b") if (prev_m is not None and d.month != prev_m) or prev_m is None and d.day <= 3 else str(d.day)
        prev_m = d.month
        xx = X(d)
        xt += f'<line class="tvr-vgrid" x1="{xx:.1f}" y1="{T:.0f}" x2="{xx:.1f}" y2="{T+PH:.1f}"/>'
        xt += f'<text class="tvr-xlab" x="{xx:.1f}" y="{H-8:.0f}" text-anchor="{"start" if d == t0 else "middle"}">{lab}</text>'
        d += _td(days=stepd)
    # the current-value pill on the right axis
    last_y = Y(ys[-1])
    pill = (f'<rect class="{"tvr-pill-g" if ys[-1] >= 0 else "tvr-pill-r"}" x="{L+PW+2:.1f}" y="{last_y-8:.1f}" width="{R-4:.0f}" height="16" rx="2"/>'
            f'<text class="tvr-pilltxt" x="{L+PW+6:.1f}" y="{last_y+3.5:.1f}">{ys[-1]:,.2f}</text>')
    # CSS-only crosshair, one strip per sampled point; a fixed readout box
    hstep = max(1, len(ts) // 110)
    hidx = list(range(0, len(ts), hstep))
    if hidx[-1] != len(ts) - 1: hidx.append(len(ts) - 1)
    labels = [_tvr_date(ts[i]) + "  " + _tvr_usd(ys[i], signed=True) for i in hidx]
    box_w = 6.4 * max(len(t) for t in labels) + 16
    box_x, box_y = L + 8, T + 2
    hover = f'<rect class="hv-box" x="{box_x:.1f}" y="{box_y:.1f}" width="{box_w:.1f}" height="20" rx="3"/>'
    for pos, i in enumerate(hidx):
        x = X(ts[i]); y = Y(ys[i])
        x_prev = X(ts[hidx[pos-1]]) if pos > 0 else L
        x_next = X(ts[hidx[pos+1]]) if pos < len(hidx)-1 else L + PW
        x0 = (x_prev + x) / 2; x1 = (x + x_next) / 2
        hover += (f'<g class="hp"><rect class="hp-hit" x="{x0:.1f}" y="{T:.0f}" width="{max(0.5, x1-x0):.1f}" height="{PH:.1f}"/>'
                  f'<g class="hv"><line class="hv-line" x1="{x:.1f}" y1="{T:.0f}" x2="{x:.1f}" y2="{T+PH:.1f}"/>'
                  f'<circle class="hv-dot" cx="{x:.1f}" cy="{y:.1f}" r="3"/>'
                  f'<text class="hv-txt" x="{box_x+8:.1f}" y="{box_y+14:.1f}">{labels[pos]}</text></g></g>')
    hover = f'<g class="hp-all">{hover}</g>'
    return f"""<div class="tvr-perf">
    <div class="tvr-legend">
      <span class="tvr-lg"><i class="tvr-sw tvr-sw-g"></i>Cumulative PnL</span>
      <span class="tvr-lg tvr-lg-off"><i class="tvr-sw tvr-sw-x"></i>Buy and hold<svg class="tvr-eye" viewBox="0 0 16 16" aria-hidden="true"><path d="M1 8s2.5-4.5 7-4.5S15 8 15 8s-2.5 4.5-7 4.5S1 8 1 8z"/><circle cx="8" cy="8" r="2"/><path d="M2 14 14 2"/></svg></span>
      <span class="tvr-lg"><i class="tvr-sw tvr-sw-b"></i>{bars_lab}</span>
      <span class="tvr-lg"><i class="tvr-sw tvr-sw-s"></i>Run-ups and drawdowns</span>
      <span class="tvr-lg tvr-lg-more"><svg class="tvr-caret" viewBox="0 0 12 12" aria-hidden="true"><path d="M2 8l4-4 4 4"/></svg></span>
    </div>
    <svg class="tvr-svg" viewBox="0 0 560 300" role="img" aria-label="Cumulative profit and loss with per-trade bars, {tr['full']['n']} closed trades" focusable="false">
      {grid}{xt}
      {bars}{strip}
      <path class="tvr-line" d="M{eq_pts}" fill="none"/>
      {pill}
      {hover}
    </svg>
  </div>"""

# ── Profits and losses: mirrored bars per signal / per side ──
def _pl_rows(groups, total_scale):
    out = ""
    for lab, a in groups:
        gl, gp = a["gl"], a["gp"]
        lw = 150.0 * gl / total_scale
        rw = 150.0 * gp / total_scale
        out += (f'<div class="tvr-plr"><span class="tvr-pll">{esc(lab)}</span>'
                f'<svg class="tvr-plsvg" viewBox="0 0 300 12" preserveAspectRatio="none" aria-hidden="true" focusable="false">'
                f'<rect class="tvr-r" x="{150-lw:.1f}" y="1" width="{lw:.1f}" height="10"/>'
                f'<rect class="tvr-g" x="150" y="1" width="{rw:.1f}" height="10"/>'
                f'<line class="tvr-mid" x1="150" y1="0" x2="150" y2="12"/></svg>'
                f'<span class="tvr-pln {_sgn(a["net"])}" title="gross profit {_tvr_usd(gp)} · gross loss {_tvr_usd(-gl)}">{_tvr_usd(a["net"], signed=True)}</span></div>')
    return out

def _profits_losses(rows, slug):
    all_a = _agg(rows)
    scale = max(all_a["gp"], all_a["gl"], 1.0)
    by_sig = {}
    for r in rows:
        by_sig.setdefault(r["sig"] or "Entry", []).append(r)
    sigs = sorted(by_sig.items(), key=lambda kv: -len(kv[1]))
    groups = [("All signals", all_a)]
    tail = []
    for i, (sig, rr) in enumerate(sigs):
        if i < 8:
            groups.append((sig, _agg(rr)))
        else:
            tail.extend(rr)
    if tail:
        groups.append((f"Other • {len(sigs) - 8}", _agg(tail)))
    sides = [("Long", _agg([r for r in rows if r["side"] == "L"])),
             ("Short", _agg([r for r in rows if r["side"] == "S"]))]
    inputs, nav = _pill_tabs("pl", slug, [("sig", "By signals", True), ("side", "By side", True)])
    return f"""<div class="tvr-sec">
      <div class="tvr-h2">Profits and losses<span class="tvr-info" title="Gross loss (red, left) and gross profit (green, right) per entry signal, net on the right">i</span></div>
      <div class="tvr-sub tvr-sub-pl">{inputs}{nav}
        <div class="tvr-sp">{_pl_rows(groups, scale)}</div>
        <div class="tvr-sp">{_pl_rows([("All", all_a)] + sides, scale)}</div>
      </div>
    </div>"""

def _periodical(rows):
    months = {}
    for r in rows:
        months.setdefault(r["d"].strftime("%Y-%m"), []).append(r)
    body = ""
    for ym in sorted(months):
        a = _agg(months[ym])
        import datetime as _dt
        lab = _dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%b %Y")
        body += (f'<tr><th scope="row">{lab}</th>'
                 f'<td class="{_sgn(a["net"])}">{_tvr_usd(a["net"], signed=True)}</td>'
                 f'<td class="{_sgn(a["net"])}">{_tvr_pct(100.0 * a["net"] / INITIAL_CAPITAL, signed=True)}</td>'
                 f'<td>{a["n"]:,}</td><td>{a["winrate"]:.2f}%</td>'
                 f'<td>{a["pf"]:.3f}</td><td class="tv-neg">{_tvr_usd(-a["dd"]) if a["dd"] else "0.00 USD"}</td></tr>')
    return f"""<div class="screener" tabindex="0" role="region" aria-label="Monthly results, scrolls horizontally">
      <table class="tvt-table tvr-table">
        <caption class="sr-only">Monthly results across the best window</caption>
        <thead><tr><th scope="col">Period</th><th scope="col">Net PnL</th><th scope="col">Return</th><th scope="col">Trades</th><th scope="col">Profitable</th><th scope="col">Profit factor</th><th scope="col">Max drawdown</th></tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
    <p class="tvt-note">Return is the month&rsquo;s net over the {INITIAL_CAPITAL/1000:.0f} K USD initial capital. Drawdown is the month&rsquo;s own closed-trade drawdown.</p>"""

def _breakdown_cells(a):
    comm = a["commission"]
    load = (100.0 * comm / a["gp"]) if (comm is not None and a["gp"]) else None
    return (f'<div class="tvr-cells">'
            + _cell("Gross profit", _tvr_usd(a["gp"]), "tv-pos", _tvr_pct(100.0 * a["gp"] / INITIAL_CAPITAL), "tv-pos")
            + _cell("Gross loss", _tvr_usd(a["gl"]), "tv-neg", _tvr_pct(100.0 * a["gl"] / INITIAL_CAPITAL), "tv-neg")
            + _cell("Profit factor", f'{a["pf"]:.3f}')
            + _cell("Commission load", _tvr_pct(load) if load is not None else "&mdash;", "", (_tvr_usd(comm) if comm is not None else ""), "",
                    title=f"commissions {COMMISSION_RT:.2f} USD per contract round turn, as a share of gross profit")
            + '</div>')

def _histogram(rows, slug):
    rets = [r for r in rows if r["ret"] is not None]
    if len(rets) < 5:
        return '<p class="tvt-note">Return distribution needs per-trade return data.</p>'
    vals = [r["ret"] for r in rets]
    lo, hi = min(vals), max(vals)
    binw = 0.05
    while (hi - lo) / binw > 70:
        binw *= 2
    import math as _m
    b0 = _m.floor(lo / binw); b1 = _m.floor(hi / binw)
    counts = {}
    for v in vals:
        k = _m.floor(v / binw)
        counts[k] = counts.get(k, 0) + 1
    nb = b1 - b0 + 1
    W, H = 300.0, 150.0
    L, R, T, B = 6.0, 6.0, 8.0, 22.0
    PW, PH = W - L - R, H - T - B
    cmax = max(counts.values())
    bwid = PW / nb
    bars = ""
    for k in range(b0, b1 + 1):
        c = counts.get(k, 0)
        if not c: continue
        h = PH * c / cmax
        x = L + (k - b0) * bwid
        cls = "tvr-g" if (k * binw) >= 0 else "tvr-r"
        bars += f'<rect class="{cls}" x="{x+0.5:.1f}" y="{T+PH-h:.1f}" width="{max(bwid-1,0.8):.1f}" height="{h:.1f}"><title>{k*binw:.2f}% to {(k+1)*binw:.2f}%: {c} trades</title></rect>'
    def XV(v): return L + (v / binw - b0) * bwid
    losers = [v for v in vals if v < 0]; winners = [v for v in vals if v > 0]
    al = sum(losers) / len(losers) if losers else 0.0
    aw = sum(winners) / len(winners) if winners else 0.0
    marks = ""
    for v in (al, aw):
        if lo <= v <= hi + binw:
            marks += f'<line class="tvr-avg" x1="{XV(v):.1f}" y1="{T:.0f}" x2="{XV(v):.1f}" y2="{T+PH:.1f}"/>'
    # a few x labels
    ticks = sorted({b0, 0, b1 + 1} | {b0 + (b1 + 1 - b0) * i // 4 for i in range(1, 4)})
    # labels need ~46 units of room; zero always keeps its label
    keep = []
    for k in ticks:
        x = L + (k - b0) * bwid
        if keep and x - keep[-1][1] < 46:
            if k == 0:
                keep.pop()
            else:
                continue
        keep.append((k, x))
    labs = ""
    for k, x in keep:
        anchor = "start" if k == b0 else ("end" if k == b1 + 1 else "middle")
        labs += f'<text class="tvr-xlab" x="{x:.1f}" y="{H-6:.0f}" text-anchor="{anchor}">{k*binw:.2f}%</text>'
    zero_x = XV(0.0)
    return f"""<svg class="tvr-hist" viewBox="0 0 300 150" role="img" aria-label="Distribution of per-trade returns" focusable="false">
        <line class="tvr-grid" x1="{L:.0f}" y1="{T+PH:.1f}" x2="{L+PW:.1f}" y2="{T+PH:.1f}"/>
        <line class="tvr-vgrid" x1="{zero_x:.1f}" y1="{T:.0f}" x2="{zero_x:.1f}" y2="{T+PH:.1f}"/>
        {bars}{marks}{labs}
      </svg>
      <p class="tvr-hleg"><i class="tvr-sw tvr-sw-r"></i>Losers <i class="tvr-sw tvr-sw-g"></i>Winners
        <span class="tvr-hsep">|</span><i class="tvr-dash"></i>Average loss <b>{_tvr_pct(al)}</b>
        <i class="tvr-dash"></i>Average profit <b>{_tvr_pct(aw)}</b></p>"""

def _donut(a):
    n = max(1, a["n"])
    w, l, b = 100.0 * a["wins"] / n, 100.0 * a["losses"] / n, 100.0 * a["be"] / n
    return f"""<div class="tvr-donut">
      <svg viewBox="0 0 120 120" role="img" aria-label="{a['n']} trades: {a['wins']} winners, {a['losses']} losers, {a['be']} breakeven" focusable="false">
        <circle class="tvr-dn-bg" cx="60" cy="60" r="46" pathLength="100"/>
        <circle class="tvr-dn-w" cx="60" cy="60" r="46" pathLength="100" stroke-dasharray="{w:.2f} {100-w:.2f}" stroke-dashoffset="25"/>
        <circle class="tvr-dn-l" cx="60" cy="60" r="46" pathLength="100" stroke-dasharray="{l:.2f} {100-l:.2f}" stroke-dashoffset="{25-w:.2f}"/>
        <circle class="tvr-dn-b" cx="60" cy="60" r="46" pathLength="100" stroke-dasharray="{b:.2f} {100-b:.2f}" stroke-dashoffset="{25-w-l:.2f}"/>
        <text class="tvr-dn-n" x="60" y="58" text-anchor="middle">{a['n']:,}</text>
        <text class="tvr-dn-t" x="60" y="72" text-anchor="middle">Total trades</text>
      </svg>
      <ul class="tvr-dl">
        <li><i class="tvr-sw tvr-sw-g"></i><span>Winners</span><b>{a['wins']:,} trades</b><em>{w:.2f}%</em></li>
        <li><i class="tvr-sw tvr-sw-r"></i><span>Losers</span><b>{a['losses']:,} trades</b><em>{l:.2f}%</em></li>
        <li><i class="tvr-sw tvr-sw-x"></i><span>Breakevens</span><b>{a['be']:,} trades</b><em>{b:.2f}%</em></li>
      </ul>
    </div>"""

def _streaks(rows):
    best = {"w": 0, "l": 0}; cur = {"w": 0, "l": 0}
    wsum = lsum = 0.0; bw_sum = bl_sum = 0.0
    runs_w, runs_l = [], []
    last = None; run = 0
    for r in rows:
        k = "w" if r["pnl"] > 0 else ("l" if r["pnl"] < 0 else None)
        if k is None:
            continue
        if k == last:
            run += 1
        else:
            if last == "w": runs_w.append(run)
            elif last == "l": runs_l.append(run)
            run = 1; last = k
        cur[k] = run; cur["l" if k == "w" else "w"] = 0
        if k == "w":
            wsum = wsum + r["pnl"] if run > 1 else r["pnl"]
            if run > best["w"]: best["w"], bw_sum = run, wsum
        else:
            lsum = lsum + r["pnl"] if run > 1 else r["pnl"]
            if run > best["l"]: best["l"], bl_sum = run, lsum
    if last == "w": runs_w.append(run)
    elif last == "l": runs_l.append(run)
    avg_w = sum(runs_w) / len(runs_w) if runs_w else 0.0
    avg_l = sum(runs_l) / len(runs_l) if runs_l else 0.0
    return f"""<div class="tvr-cells">
      {_cell("Max consecutive wins", f'{best["w"]}', "tv-pos", _tvr_usd(bw_sum, signed=True), "tv-pos")}
      {_cell("Max consecutive losses", f'{best["l"]}', "tv-neg", _tvr_usd(bl_sum, signed=True), "tv-neg")}
      {_cell("Average win streak", f'{avg_w:.2f}', "", f'{len(runs_w)} streaks')}
      {_cell("Average loss streak", f'{avg_l:.2f}', "", f'{len(runs_l)} streaks')}
    </div>
    <p class="tvt-note">Streaks count consecutive winning or losing closed trades in exit order across the best window; the money figure is the net of the longest streak.</p>"""

def tester_block(p):
    b, f = p["best"]["stats"], (p.get("full") or {}).get("stats", {})
    slug = p["slug"]
    tr = load_trades_data(slug)
    if not tr:
        return f"""<div class="tvt tvr" id="tester">
  <div class="tvr-top"><span class="tvr-strat">{esc(p["name"])}</span><span class="tvr-chip">{esc(p.get("window", ""))}</span></div>
  <div class="tvt-pane tvr-p1 tvr-open">
    <div class="tvr-h1">Key stats</div>
    <div class="tvr-cells">{_cell("Total PnL", esc(b.get("Net", "")), "tv-pos")}{_cell("Max drawdown", esc(b.get("Max DD", "")))}{_cell("Profitable trades", esc(b.get("Win", "")))}{_cell("Profit factor", esc(b.get("PF", "")))}</div>
    {chart_figure(p)}
    <p class="tvt-note">Best window &middot; {esc(p.get("window", ""))}. Equity curve is illustrative, fitted to the published stats, until the trade-level export replaces it.</p>
  </div>
</div>"""
    import datetime as _dt
    rows, exact = _window_rows(tr, "best")
    a = _agg(rows)
    wb, wf = window_trade_stats(tr, "best"), window_trade_stats(tr, "full")
    net, dd = (tr["best"]["net"], tr["best"]["dd"]) if exact else (a["net"], a["dd"])
    ws, we = _dt.date.fromisoformat(tr["best"]["start"]), _dt.date.fromisoformat(tr["best"]["end"])
    fs, fe = _dt.date.fromisoformat(tr["full"]["start"]), _dt.date.fromisoformat(tr["full"]["end"])
    mult = p.get("mult", 1)
    pnls = [r["pnl"] for r in rows]
    mean = sum(pnls) / len(pnls)
    sd = (sum((x - mean) ** 2 for x in pnls) / max(1, len(pnls) - 1)) ** 0.5
    outliers = [x for x in pnls if abs(x - mean) > 3 * sd]
    out_sum = sum(outliers)
    lw = max(rows, key=lambda r: r["pnl"]); ll = min(rows, key=lambda r: r["pnl"])
    key_cells = (
        _cell("Total PnL", _tvr_usd(net, signed=True), _sgn(net), _tvr_pct(100.0 * net / INITIAL_CAPITAL, signed=True), _sgn(net))
        + _cell("Max drawdown", _tvr_usd(dd), "", _tvr_pct(100.0 * dd / INITIAL_CAPITAL), "",
                title="closed-trade drawdown across the best window")
        + _cell("Profitable trades", f'{a["winrate"]:.2f}%', "", f'{a["wins"]:,}/{a["n"]:,}')
        + _cell("Profit factor", f'{a["pf"]:.3f}'))
    trade_cells = (
        _cell("Expected payoff", _tvr_usd(a["avg"]), _sgn(a["avg"]), _tvr_pct(a["avg_ret"]) if a["avg_ret"] is not None else "", _sgn(a["avg"]),
              title="average net per closed trade; the percentage is the average per-trade return on position value")
        + _cell("Outliers PnL", _tvr_usd(out_sum, signed=True), _sgn(out_sum), _tvr_pct(100.0 * out_sum / INITIAL_CAPITAL, signed=True), _sgn(out_sum),
                title=f"net of the {len(outliers)} trades beyond three standard deviations of the mean trade")
        + _cell("Largest profit", _tvr_usd(lw["pnl"], signed=True), "tv-pos", _tvr_pct(lw["ret"], signed=True) if lw["ret"] is not None else "", "tv-pos")
        + _cell("Largest loss", _tvr_usd(ll["pnl"], signed=True), "tv-neg", _tvr_pct(ll["ret"], signed=True) if ll["ret"] is not None else "", "tv-neg"))
    perf_in, perf_nav = _pill_tabs("pa", slug, [("bd", "Breakdown", True), ("pd", "Periodical", True),
                                                ("bm", "Benchmarking", False), ("mu", "Margin usage", False), ("gd", "Growth and decline", False)])
    perf_nav_static = ('<nav class="tvr-pills"><label for="tvt-%s-ps" class="tvr-pill tvr-pill-on">Breakdown</label>'
                       '<label for="tvt-%s-ps" class="tvr-pill">Periodical</label>'
                       '<span class="tvr-pill tvr-pill-off">Benchmarking</span><span class="tvr-pill tvr-pill-off">Margin usage</span>'
                       '<span class="tvr-pill tvr-pill-off">Growth and decline</span></nav>' % (slug, slug))
    tr_in, tr_nav = _pill_tabs("ta", slug, [("ds", "Distribution", True), ("st", "Streaks", True),
                                            ("tp", "Time patterns", False), ("dt", "Trades analysis details", wb is not None and wf is not None)])
    details = ""
    if wb and wf:
        ta_rows = (
            _ta_row("Total trades", f'{wb["n"]:,}', f'{wf["n"]:,}')
            + _ta_row("Winning trades", f'{wb["wins"]:,}', f'{wf["wins"]:,}')
            + _ta_row("Losing trades", f'{wb["losses"]:,}', f'{wf["losses"]:,}')
            + _ta_row("Percent profitable", f'{wb["winrate"]:.2f}%', f'{wf["winrate"]:.2f}%', "tv-pos")
            + _ta_row("Avg P&amp;L per trade", _tvr_usd(wb["avg"]), _tvr_usd(wf["avg"]), _sgn(wb["avg"]))
            + _ta_row("Avg winning trade", _tvr_usd(wb["aw"]), _tvr_usd(wf["aw"]), "tv-pos")
            + _ta_row("Avg losing trade", _tvr_usd(wb["al"]), _tvr_usd(wf["al"]), "tv-neg")
            + _ta_row("Ratio avg win / avg loss", f'{wb["ratio"]:.3f}', f'{wf["ratio"]:.3f}')
            + _ta_row("Largest winning trade", _tvr_usd(wb["lw"]), _tvr_usd(wf["lw"]), "tv-pos")
            + _ta_row("Largest losing trade", _tvr_usd(wb["ll"]), _tvr_usd(wf["ll"]), "tv-neg")
        )
        details = f"""<div class="tvr-sp">
          <div class="screener" tabindex="0" role="region" aria-label="Trades analysis table, scrolls horizontally">
          <table class="tvt-table tvr-table">
            <caption class="sr-only">Trades analysis, best window beside the full record</caption>
            <thead><tr><th scope="col">Metric</th><th scope="col">Best window</th><th scope="col">Full record</th></tr></thead>
            <tbody>{ta_rows}</tbody>
          </table>
          </div>
          <p class="tvt-note">Derived from the published trade list. Each window slice reproduces its published trade count and net exactly, or these rows do not render.</p>
        </div>"""
    win_lab = f"{_tvr_date(ws)} — {_tvr_date(we)}" if exact else f"{_tvr_date(fs)} — {_tvr_date(fe)}"
    basis = (f'Figures: best window {_tvr_date(ws)} &rarr; {_tvr_date(we)} ({a["n"]:,} closed trades)' if exact
             else f'Figures: full record ({a["n"]:,} closed trades)')
    caption = (f'{basis} at Multiplier {mult}, stated against {INITIAL_CAPITAL/1000:.0f} K USD initial capital. '
               f'Chart: the full record, {_tvr_date(fs)} &rarr; {_tvr_date(fe)} ({tr["full"]["n"]:,} trades). '
               f'Commissions and slippage modeled.')
    return f"""<div class="tvt tvr" id="tester">
  <input type="radio" name="tvt-{slug}" id="tvt-{slug}-ov" class="tvt-r" checked>
  <input type="radio" name="tvt-{slug}" id="tvt-{slug}-ps" class="tvt-r">
  <input type="radio" name="tvt-{slug}" id="tvt-{slug}-ta" class="tvt-r">
  <input type="radio" name="tvt-{slug}" id="tvt-{slug}-lt" class="tvt-r">
  <div class="tvr-top">
    <span class="tvr-strat">{esc(p["name"])}</span>
    <span class="tvr-chip"><svg class="tvr-cal" viewBox="0 0 16 16" aria-hidden="true"><rect x="2" y="3" width="12" height="11" rx="1.5"/><path d="M2 7h12M5 1.5v3M11 1.5v3"/></svg>{win_lab}<b class="tvr-deep">DEEP</b></span>
    <span class="tvr-chip">{INITIAL_CAPITAL/1000:.0f} K USD</span>
    <span class="tvr-chip">Default detalization</span>
    <span class="tvr-chip">Script execution <b class="tvr-circ">1</b></span>
  </div>
  <div class="tvt-tabs tvr-tabs">
    <label for="tvt-{slug}-ov" class="tvt-tab">Overview</label>
    <label for="tvt-{slug}-ps" class="tvt-tab">Performance</label>
    <label for="tvt-{slug}-ta" class="tvt-tab">Trades</label>
    <label for="tvt-{slug}-lt" class="tvt-tab">List of trades</label>
  </div>
  <div class="tvt-pane tvr-p1">
    <div class="tvr-h1">Key stats</div>
    <div class="tvr-cells tvr-key">{key_cells}</div>
    <div class="tvr-h1">Performance<span class="tvr-info" title="Cumulative net profit across the full record, with the per-trade results along the bottom">i</span></div>
    {real_chart(p, tr)}
    <div class="tvr-h1">Performance analysis</div>
    {perf_nav_static}
    {_breakdown_cells(a)}
    <p class="tvt-note">{caption}</p>
  </div>
  <div class="tvt-pane tvr-p2">
    <div class="tvr-h1">Performance analysis</div>
    <div class="tvr-sub">{perf_in}{perf_nav}
      <div class="tvr-sp">{_breakdown_cells(a)}{_profits_losses(rows, slug)}</div>
      <div class="tvr-sp">{_periodical(rows)}</div>
    </div>
    <p class="tvt-note">{caption}</p>
  </div>
  <div class="tvt-pane tvr-p3">
    <div class="tvr-h1">Trades analysis</div>
    <div class="tvr-sub">{tr_in}{tr_nav}
      <div class="tvr-sp">
        <div class="tvr-cells">{trade_cells}</div>
        <div class="tvr-two">
          <div class="tvr-panel"><div class="tvr-h2">Returns distribution</div>{_histogram(rows, slug)}</div>
          <div class="tvr-panel"><div class="tvr-h2">Trades distribution</div>{_donut(a)}</div>
        </div>
      </div>
      <div class="tvr-sp">{_streaks(rows)}</div>
      {details}
    </div>
    <p class="tvt-note">{caption}</p>
  </div>
  {trades_table(tr, slug)}
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
        <stop offset="0" stop-color="#56c8a2" stop-opacity=".22"/>
        <stop offset="1" stop-color="#56c8a2" stop-opacity="0"/>
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

BASE_DD = CAT.get("baseline_dd", 5000)

def baseline(p, stats_key="best"):
    """Net normalised to a fixed drawdown, so products are comparable to each
    other. Raw net is not: it mixes drawdown depth AND position size."""
    s = (p.get(stats_key) or {}).get("stats", {})
    r = num(s.get("RoDD", 0))
    return r * BASE_DD if r else 0

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
        rec_tag = '<span class="ro-rec">our pick</span>' if rec else ''
        labels += (f'<label for="ro-{slug}-{i}" class="ro-notch{" ro-notch-rec" if rec else ""}">{rec_tag}<span class="ro-tick" aria-hidden="true"></span>'
                   f'<span class="ro-amt">{lab}</span></label>')
        if state == "red":
            body = (f'<span class="ro-flag">Not built for this size</span> The deepest published max drawdown '
                    f'({usd(red_at)}, {guard_src}) exceeds a {lab} budget &mdash; this sizing would not have '
                    f'survived the sample. Some systems are not meant to run this small.')
        else:
            proj_full = rodd_full * C
            both = (f' Over the full record, <b>{usd(proj_full)}</b>.' if rodd_full and abs(rodd_full - rodd) > 0.01 else '')
            body = (f'A drawdown budget of <b>{lab}</b> historically returned <b class="ro-ret">~{usd(proj)}</b> '
                    f'over the best window.{both} Past results, not a forecast.')
            if rec:
                body = ('<span class="ro-flag ro-flag-rec">Recommended</span> The smallest budget that clears '
                        f'the deepest published drawdown ({usd(red_at)}, {guard_src}). ' + body)
            if state == "amb":
                body = (f'<span class="ro-flag">Thin cushion</span> The deepest published drawdown ({usd(red_at)}, '
                        f'{guard_src}) is more than half this budget &mdash; one bad stretch uses most of your '
                        'room. ' + body)
        outs += f'<div class="ro-out ro-out-{i}">{body}</div>'
    if not default_set:  # everything red/amber — check the last notch
        radios = radios.replace(f'id="ro-{slug}-{len(NOTCHES)}" class', f'id="ro-{slug}-{len(NOTCHES)}" checked class', 1)
    return f"""<div class="rodd" aria-label="Return-on-drawdown sizing menu">
  <div class="rodd-head">
    <span class="rodd-title">Sizing</span>
    <span class="rodd-fig">{pct(b.get("RoDD",""))}</span>
  </div>
  <p class="rodd-why"><b>RoDD is the metric this catalog is priced on.</b> Profit factor says the engine works;
  RoDD says what it costs to hold: net profit divided by the worst peak-to-valley drawdown.
  This system&rsquo;s window ({esc(b.get("Months",""))} months): {esc(net)} net &divide; {usd(dd)} max drawdown
  = <b>{pct(b.get("RoDD",""))} return on drawdown</b>.
  Slide your drawdown budget &mdash; the projection scales with it, and so does the pain.</p>
  {radios}
  <div class="ro-track" aria-hidden="false">{labels}</div>
  <div class="ro-outs">{outs}</div>
  <p class="ro-note">Linear scaling of the published window; not a projection of future results. See the disclaimer below.</p>
</div>"""

def legs_block(p):
    """Legs entries are either [session-label, slug] — a leg also sold as its own
    product, rendered as a link with the product's display name — or a plain
    string, an exclusive leg rolled up into one '+N exclusive' cell (names of
    exclusive legs stay off the page)."""
    if not p.get("legs"): return ""
    name_by_slug = {s["slug"]: s["name"] for s in CAT["strategies"]}
    linked = [l for l in p["legs"] if isinstance(l, list)]
    exclusive_n = sum(1 for l in p["legs"] if not isinstance(l, list))
    cells = ""
    parked = 0
    for i, (label, slug) in enumerate(linked, 1):
        prod = name_by_slug.get(slug, "")
        if slug in name_by_slug:
            inner = (f'<a class="leg-link" href="/strategies/{slug}.html">'
                     f'<span class="leg-name">{esc(label)}</span>'
                     f'<span class="leg-prod">{esc(prod)}</span></a>')
        else:
            # leg sold standalone in the past but not listed right now (parked
            # in drafts): never emit a link to a page that does not exist
            parked += 1
            inner = f'<span class="leg-link"><span class="leg-name">{esc(label)}</span></span>'
        cells += f'<div class="leg"><span class="leg-n">{i:02d}</span>{inner}</div>'
    if exclusive_n:
        plural = "strategies" if exclusive_n != 1 else "strategy"
        cells += (f'<div class="leg leg-x"><span class="leg-n">+{exclusive_n}</span>'
                  f'<span class="leg-name">exclusive book {plural}</span></div>')
    total = len(p["legs"])
    named = "The linked legs above" if parked else "The named legs above"
    note_tail = (f" {named} are also sold as standalone subscriptions; the exclusive legs trade only inside the book."
                 if linked and exclusive_n else "")
    return f"""<div class="record">
  <div class="record-title">Inside the book &middot; {total} engines, one router</div>
  <div class="legs">{cells}</div>
  <p class="record-note">Each leg is a standalone engine trading its own session; the router allocates between them.
  Every figure on this page is the book as a whole, not any single leg. Composition dials are proprietary.{note_tail}</p>
</div>"""

def sep_block(p):
    if not p.get("sep"): return ""
    items = "".join(f'<li><svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg><span>{s}</span></li>'
                    for s in p["sep"])
    return f"""<div class="record sep-panel">
  <div class="record-title">Why this one</div>
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
THEMED = {p["slug"] for p in CAT["strategies"]}
THEMED |= {b["slug"] for b in CAT["books"]}

os.makedirs(os.path.join(BASE, "strategies"), exist_ok=True)
urls = ["/", "/plan.html", "/terms.html", "/privacy.html"]

def _fmt_iso(iso):
    import datetime as _dt
    try:
        return _dt.date.fromisoformat(iso).strftime("%d %b %Y")
    except Exception:
        return iso

def write_window_csv(p, tr):
    """Best-window trade list as a downloadable CSV (owner 2026-09-03). Rows are the
    published record only — exit day, entry/exit price, net P&L at the shown multiplier."""
    if not tr or not tr.get("trades"):
        return None, 0
    import datetime as _dt
    bs, be = tr["best"]["start"], tr["best"]["end"]
    d0, d1 = _dt.date.fromisoformat(bs), _dt.date.fromisoformat(be)
    cols = tr.get("trades_columns") or ["exit_day", "entry_px", "exit_px", "net_pnl_usd"]
    rows = []
    for r in tr["trades"]:
        try:
            d = _dt.datetime.strptime(r[0], "%d %b %y").date()
        except Exception:
            rows.append(r); continue
        if d0 <= d <= d1:
            rows.append(r)
    os.makedirs(os.path.join(BASE, "strategies", "data"), exist_ok=True)
    rel = f"/strategies/data/{p['slug']}-best-window-trades.csv"
    with open(os.path.join(BASE, rel.lstrip("/")), "w", encoding="utf-8", newline="") as fh:
        fh.write("# " + p["name"] + " (" + p["actual"] + ") - best return-on-drawdown window "
                 + _fmt_iso(bs) + " to " + _fmt_iso(be) + " - closed trades at Multiplier "
                 + str(p.get("mult", 1)) + " - hypothetical backtested results, commissions and slippage modeled\n")
        fh.write(",".join(cols) + "\n")
        for r in rows:
            fh.write(",".join(str(x) for x in r) + "\n")
    return rel, len(rows)

def window_block(p, tr):
    """'This strategy was optimized from … to …' + the best-RoDD window + the CSV link."""
    ow = p.get("opt_window") or {}
    if not tr or not ow:
        return ""
    bs, be = _fmt_iso(tr["best"]["start"]), _fmt_iso(tr["best"]["end"])
    rel, n = write_window_csv(p, tr)
    link = (f'<p class="pdp-csv-line"><a class="pdp-csv" href="{rel}" download>Download the trade list for this window '
            f'(CSV, {n:,} trades)</a></p>') if rel else ""
    return (f'<div class="pdp-window"><p><strong>This strategy was optimized from {esc(ow.get("start",""))} to '
            f'{esc(ow.get("end",""))}.</strong> {bs} to {be} is the best return-on-drawdown timeframe we have, '
            f'and it is the window displayed on the chart and in the figures on this page.</p>{link}</div>')

def product_page(p, is_book):
    path = f"/strategies/{p['slug']}.html"
    urls.append(path)
    b = p["best"]["stats"]
    mdesc = (f"{p['name']} ({p['actual']}): {rodd_mo_pct(b)} avg monthly return on drawdown "
             f"({pct(b.get('RoDD',''))} over {b.get('Months','')} months), "
             f"PF {b.get('PF','')}, {b.get('Trades','')} trades. Backtest-verified on real TradingView data. "
             f"TradingView invite-only script, activated within 24h.")
    crumb_root = ('<a href="/strategies/the-books.html">The Books</a>' if is_book
                  else '<a href="/">Strategies</a>')
    _tr = load_trades_data(p["slug"])
    main_col = window_block(p, _tr) + "\n" + rodd_menu(p) + "\n" + tester_block(p) + "\n" + (
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
          <span class="pdp-note">{esc(p['meta'])}</span>
        </div>
        <div class="pdp-hero"><b>{rodd_mo_pct(b)}</b><span>per month &middot; avg monthly return on drawdown</span>
          <em class="pdp-hero-sub">{pct(b.get('RoDD',''))} return on drawdown over {esc(b.get('Months',''))} months</em>
          <em class="pdp-hero-sub">Return on drawdown = net profit &divide; maximum drawdown over the window, shown per month of the record.</em>
          <em class="pdp-hero-sub">{usd(baseline(p))} on a {usd(BASE_DD)} drawdown</em>
          {f'<em class="pdp-hero-sub">Shown at Multiplier {p["mult"]} &middot; drawdown held under $10,000 &middot; RoDD is size-independent</em>' if p.get('mult') else ''}</div>
      </div>

      <div class="pdp-cols">
        <div class="pdp-main">
        {main_col}
        </div>
        <div class="pdp-side">
        {buybox(p['name'], f"{p['price']:,}", p['name'] + " / " + p['actual'], xsell=xsell,
                href=(p.get("whop") or WHOP_STORE))}
        {sep_block(p)}
        </div>
      </div>

      <div class="pdp-wide">{cal_col}</div>

      <div class="pdp-disclaim">
        <p class="disclaim-sm">{esc(DISCLAIMER)}</p>
      </div>

      <a class="backlink" href="{'/strategies/the-books.html' if is_book else '/'}">&larr; {'The Books' if is_book else 'All strategies'}</a>
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
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Strategies</a><span class="sep">/</span>{esc(name)}</nav>
    <article class="pdp">
      <div class="pdp-head">
        <div>
          <h1>{esc(name)}</h1>
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
      <a class="backlink" href="/">&larr; All strategies</a>
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
              <p class="xsell">Questions? Ask in <a href="https://discord.gg/BBXDDn9pCD" rel="noopener">Discord</a></p>
            </aside>
          </div>

          <div class="pdp-disclaim">
            <p class="disclaim-sm">{esc(DISCLAIMER)}</p>
          </div>

          <a class="backlink" href="/">&larr; Browse the catalog</a>
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
            <a class="btn" href="/">Browse strategies</a>
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
<p><strong>2. Performs-as-Published guarantee (60 days).</strong> Every strategy is sold with a
published trade record. If, within 60 days of your first charge, the strategy running on your
TradingView chart at its default settings and our stated Properties (1-minute chart of the
instrument named on its page, commission $0.75 per contract per side, slippage 2 ticks) does not
produce the same signals as its published record for the same dates &mdash; same entry bars, same
direction, same exits &mdash; you get a full refund of everything you have paid for that product. To
claim it, send us the Strategy Tester&rsquo;s List of Trades export from your chart for any 10 or
more trading days inside your first 60 days; we compare it to the published record for those dates
and refund if they differ. What it does not cover: profit or loss (markets do not repeat; the
record is hypothetical, backtested performance), fills in your own account (broker, bridge and
slippage differ), and results produced with settings, chart, symbol or Properties other than the
published ones. One claim per customer per product; it does not extend to renewals after the 60
days.</p>
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
