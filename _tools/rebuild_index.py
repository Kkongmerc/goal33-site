import re
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
SPECIAL = CAT.get("special") or {}
def special_strip():
    """One line above the tables, all copy from catalog2 `special`; nothing when active=false."""
    if not SPECIAL.get("active"):
        return ""
    line = SPECIAL.get("line", "").replace("{pct}", str(SPECIAL.get("pct", ""))).replace("{code}", SPECIAL.get("code", ""))
    ends = f'<em>ends {esc(SPECIAL["ends"])}</em>' if SPECIAL.get("ends") else ""
    item = f'<span class="sm-i"><b>{esc(SPECIAL.get("label", "Special"))}</b> {esc(line)}{(" &middot; ends " + esc(SPECIAL["ends"])) if SPECIAL.get("ends") else ""}</span>'
    return f'<div class="special-marquee"><div class="sm-track">{item * 8}</div></div>'

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
    if p.get("kind") == "combined":
        return p["net"] / p["months"]
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

def sparkline(slug, cls="fspark", pfx="fsg", maxpts=0, pts=None):
    """Full-bleed equity curve for a flagship pane, from the real record (or the points given)."""
    if pts is None:
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

# ── product tiers (owner 2026-09-03): Books on top, then the combo sets, then singles per market ──
def kind_of(p):
    k = p.get("kind")
    if k: return k
    n = len(p.get("legs") or [])
    return "book" if n >= 5 else ("combo" if n >= 2 else "single")

def _win_days(p):
    """The best window's daily net, from the trade record."""
    tr = load_trades(p["slug"])
    if not tr: return {}
    s, e = tr["best"]["start"], tr["best"]["end"]
    return {d: v for d, v in tr["daily"].items() if s <= d <= e}

def month_extremes(p, daily=None):
    """(best, worst) calendar month of the window as ('+$12.4k', 'Mar 26') tuples."""
    daily = _win_days(p) if daily is None else daily
    months = {}
    for d, v in daily.items():
        months[d[:7]] = months.get(d[:7], 0.0) + v
    if not months: return None, None
    def fmt(ym, v):
        lab = datetime.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%b %y")
        sign = "+" if v >= 0 else "&minus;"
        a = abs(v)
        val = f"${a/1000:,.1f}k" if a >= 1000 else f"${a:,.0f}"
        return (sign + val, lab)
    hi = max(months, key=months.get); lo = min(months, key=months.get)
    return fmt(hi, months[hi]), fmt(lo, months[lo])

def dd_pair(p):
    """(drawdown at one multiple, drawdown at the published multiplier) in dollars."""
    tr = load_trades(p["slug"])
    m = int(p.get("mult") or 1)
    dk = tr["best"]["dd"] if tr else num(bs(p, "Max DD"))
    return dk / m, dk

def books_combined():
    """Both books together (Continuum + Midas), owner 2026-09-03: each book's daily series is
    taken back to ONE multiple (its published curve divided by its shown multiplier), the two 1x
    curves are merged into one equity curve, and the pair is then multiplied by the largest whole
    K that keeps the merged max drawdown under $10,000 - never below x3 (if x3 breaches $10k the
    row still ships at x3 and the drawdown says so). Net = merged sum at K; max DD from the merged
    curve at K; months = span of the merged record; trades = sum; win / PF from both lists."""
    books = [p for p in S if kind_of(p) == "book"]
    trs = [(p, load_trades(p["slug"])) for p in books]
    trs = [(p, t) for p, t in trs if t]
    if len(trs) < 2: return None
    daily1 = {}
    for p, t in trs:
        m = float(p.get("mult") or 1)
        for d, v in t["daily"].items():
            daily1[d] = daily1.get(d, 0.0) + v / m
    days = sorted(daily1)
    cum = peak = dd1 = 0.0
    for d in days:
        cum += daily1[d]; peak = max(peak, cum); dd1 = max(dd1, peak - cum)
    net1 = cum
    K = max(3, int(10000.0 // dd1)) if dd1 else 3
    daily = {d: v * K for d, v in daily1.items()}
    cum = 0.0; eq = []
    for d in days:
        cum += daily[d]; eq.append([d, round(cum, 2)])
    net, dd = net1 * K, dd1 * K
    d0 = datetime.date.fromisoformat(days[0]); d1 = datetime.date.fromisoformat(days[-1])
    months = round((d1 - d0).days / 30.44, 1) or 1.0
    pnls = [row[3] for _, t in trs for row in t["trades"]]
    wins = [x for x in pnls if x > 0]; losses = [x for x in pnls if x < 0]
    gp, gl = sum(wins), -sum(losses)
    rodd = net / dd if dd else 0.0
    return {
        "slug": "the-books", "name": " + ".join(p["name"] for p, _ in trs), "actual": "both books together, one account",
        "meta": "MNQ + MGC · 18:00 – market close", "session": "18:00 – market close", "kind": "combined",
        "price": CAT["bundles"]["books_all"]["price"], "mult": K, "mults": [(p["name"], p.get("mult")) for p, _ in trs],
        "dd1": dd1, "net1": net1,
        "legs": [], "whop": WHOP_STORE, "eq": eq, "daily": daily,
        "net": net, "dd": dd, "months": months, "rodd": rodd, "n": len(pnls),
        "best": {"stats": {"RoDD": "%.2f" % rodd, "Months": "%.1f" % months, "Win": "%.1f%%" % (100.0 * len(wins) / len(pnls)),
                           "PF": "%.2f" % (gp / gl if gl else 0), "Net": "$%.1fk" % (net / 1000), "Max DD": "$%.1fk" % (dd / 1000),
                           "Trades": "{:,}".format(len(pnls))}},
        "first": days[0], "last": days[-1],
    }

COMBINED = books_combined()
_flag_order = ["the-books", "continuum", "midas", "triad", "slipstream"]
_by = {p["slug"]: p for p in S}
if COMBINED: _by["the-books"] = COMBINED
TOP5 = [_by[s] for s in _flag_order if s in _by][:5]
if len(TOP5) < 5:
    TOP5 += [p for p in sorted(S, key=lambda x: -x["price"]) if p not in TOP5][:5 - len(TOP5)]
RODD_RANK = {p["slug"]: i + 1 for i, p in enumerate(sorted(S, key=lambda x: -num(bs(x, "RoDD"))))}
if COMBINED: RODD_RANK["the-books"] = 1

def cf_block():
    radios = '<input class="cf-r" type="radio" name="cf-sel" id="cf-0" checked>' + "".join(
        f'<input class="cf-r" type="radio" name="cf-sel" id="cf-{i+1}">' for i in range(len(TOP5)))
    panes = ""
    for i, p in enumerate(TOP5):
        rk = RODD_RANK[p["slug"]]
        tag = f"#{rk} RoDD" if rk <= 3 else "RoDD"
        href = "/#books" if p["slug"] == "the-books" else f'/strategies/{p["slug"]}.html'
        panes += (
            f'<div class="cf-pane fc-{p["slug"]}">'
            f'<a class="cf-link" href="{href}">'
            + sparkline(p["slug"], cls="cf-spark", pfx="cf-sg", maxpts=64, pts=p.get("eq"))
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
    if p.get("session"):
        return p["session"]
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

def _money_k(v):
    a = abs(v); s = "" if v >= 0 else "&minus;"
    return f"{s}${a/1000:,.1f}k" if a >= 1000 else f"{s}${a:,.0f}"

def _month_cell(t, cls):
    if not t: return '<td class="sx-f">&mdash;</td>'
    return f'<td class="sx-f {cls}">{t[0]}<small class="sx-mo">{t[1]}</small></td>'

def _rowlink(html, url):
    """Owner 2026-09-03: the whole row is clickable. Every cell's content is wrapped in a
    full-cell link to the product page (the name and price cells keep their own links)."""
    def wrap(m):
        cls, inner = m.group(1), m.group(2)
        if "sx-n" in cls or "sx-p" in cls or "<a " in inner:
            return m.group(0)
        return f'<td class="{cls}"><a class="sx-rl" href="{url}" tabindex="-1" aria-hidden="true">{inner}</a></td>'
    return re.sub(r'<td class="([^"]*)">(.*?)</td>', wrap, html, flags=re.S)

def row(p, rank, dd_cols=False):
    return _rowlink(_row(p, rank, dd_cols), "/#books" if p.get("kind") == "combined" else f'/strategies/{p["slug"]}.html')

def _row(p, rank, dd_cols=False):
    b = p["best"]["stats"]
    name = esc(p["name"])
    sub = esc(p["actual"])
    note = ""
    k = kind_of(p)
    if k == "combined":
        note = '<span class="sx-book">both books at one multiple each, merged, then &times;' + str(p["mult"]) + '</span>'
        link = f'<span class="sx-combined">{glyph("the-books", "glyph sx-g")}{name}</span>'
    else:
        if p.get("legs"):
            note = f'<span class="sx-book">{"book" if k == "book" else "combo"} · combines {len(p["legs"])} strategies</span>'
        link = f'<a class="fc-{p["slug"]}" href="/strategies/{p["slug"]}.html">{glyph(p["slug"], "glyph sx-g")}{name}</a>'
    hi, lo = month_extremes(p, p.get("daily") if k == "combined" else None)
    dd_html = ""
    if dd_cols:
        if k == "combined":
            dd_html = f'<td class="sx-f">{_money_k(p["dd1"])}</td><td class="sx-f sx-neg">{_money_k(p["dd"])}</td>'
        else:
            d1, dk = dd_pair(p)
            dd_html = f'<td class="sx-f">{_money_k(d1)}</td><td class="sx-f sx-neg">{_money_k(dk)}</td>'
    # owner 2026-09-03: a profitable worst month renders green (class chosen by sign)
    mult = ("&times;" + str(p["mult"])) if p.get("mult") else "—"
    return (
        f'<tr>'
        f'<td class="sx-r">{rank}</td>'
        f'<td class="sx-n">{link}<span class="sx-sub">{sub}</span>{note}</td>'
        f'<td class="sx-f sx-rodd">{rodd_mo_pct(b) if b.get("RoDD") else "—"}</td>'
        f'<td class="sx-f">{esc(b.get("Win", "—"))}</td>'
        f'<td class="sx-f">{esc(b.get("PF", "—"))}</td>'
        f'<td class="sx-f sx-net">{profit_cell(p)}</td>'
        + _month_cell(hi, "sx-pos" if (hi and not hi[0].startswith("&minus;")) else "sx-neg")
        + _month_cell(lo, "sx-pos" if (lo and not lo[0].startswith("&minus;")) else "sx-neg")
        + dd_html +
        f'<td class="sx-f">{mult}</td>'
        f'<td class="sx-s">{esc(session_of(p))}</td>'
        f'<td class="sx-f sx-p"><!-- WHOP: replace this product-page link with the Whop checkout link -->'
        f'<a href="{esc(buy_href(p))}" rel="noopener">${p["price"]:,}</a></td>'
        f'</tr>'
    )

def coming_soon_html():
    """Instrument sections listed as coming soon (owner 2026-09-03): construction + session + status,
    no prices or links until each passes the TradingView campaign. Driven by catalog2 `coming_soon`."""
    cs = CAT.get("coming_soon") or {}
    out = ""
    for title, rows in cs.items():
        if title.startswith("_") or not isinstance(rows, list): continue
        trs = "".join(f'<tr><td class="sx-n">{esc(r[0])}</td><td class="sx-s">{esc(r[1])}</td><td class="sx-f"><span class="sx-soon">{esc(r[2])}</span></td></tr>' for r in rows)
        out += f"""
<section class="sx-sec sx-soon-sec">
  <h2>{esc(title)} <span class="sx-soon-badge">Coming soon</span></h2>
  <p class="sx-lede-sec">Validated in the engine; now being reproduced on TradingView on the same rules as every listed strategy (drawdown under $10,000 at the shown multiplier, no result carried by a handful of trades, no break-even-stop padding). Listed here with prices once the tape passes.</p>
  <div class="sx-scroll"><table class="sx-t sx-t-soon"><thead><tr><th scope="col" class="sx-n">Construction</th><th scope="col" class="sx-s">Session (ET)</th><th scope="col" class="sx-f">Status</th></tr></thead><tbody>{trs}</tbody></table></div>
</section>"""
    return out

def table(title, rows_html, n, dd_cols=False, sec_id="", lede=""):
    dd_th = ('<th scope="col" class="sx-f"><abbr title="Max drawdown of the best window at one multiple of the product\'s own sizing">Drawdown 1&times;</abbr></th>'
             '<th scope="col" class="sx-f"><abbr title="Max drawdown of the best window at the published multiplier">Drawdown at &times;K</abbr></th>') if dd_cols else ""
    idattr = f' id="{sec_id}"' if sec_id else ""
    lede_html = f'<p class="sx-lede-sec">{lede}</p>' if lede else ""
    return f"""<section class="sx-sec"{idattr}>
  <h2>{esc(title)}</h2>{lede_html}
  <div class="sx-scroll" tabindex="0" role="region" aria-label="{esc(title)} specification table, scrolls horizontally on small screens">
  <table class="sx-t{' sx-t-wide' if dd_cols else ''}">
    <caption class="sr-only">{esc(title)}: {n} rows ranked by average monthly return on drawdown</caption>
    <thead><tr>
      <th scope="col" class="sx-r" aria-label="Rank">#</th>
      <th scope="col" class="sx-n">Strategy</th>
      <th scope="col" class="sx-f sx-rodd"><abbr title="Average monthly return on drawdown">RoDD/mo</abbr></th>
      <th scope="col" class="sx-f">Win Rate</th>
      <th scope="col" class="sx-f">Profit Factor</th>
      <th scope="col" class="sx-f sx-net"><abbr title="Average monthly net profit over the best window, at the shown multiplier">Avg Monthly Profit</abbr></th>
      <th scope="col" class="sx-f"><abbr title="Best calendar month of the best window">Best month</abbr></th>
      <th scope="col" class="sx-f"><abbr title="Worst calendar month of the best window">Worst month</abbr></th>
      {dd_th}
      <th scope="col" class="sx-f"><abbr title="Multiplier the published figures are shown at">Mult</abbr></th>
      <th scope="col" class="sx-s">Session (ET)</th>
      <th scope="col" class="sx-f sx-p">$ / mo</th>
    </tr></thead>
    <tbody>{rows_html}</tbody>
  </table>
  </div>
</section>"""

books = sorted([p for p in S if kind_of(p) == "book"], key=lambda x: -x["price"])
book_list = ([COMBINED] if COMBINED else []) + books
combos = [p for p in S if kind_of(p) == "combo"]
mnq = [p for p in S if kind_of(p) == "single" and market_of(p) == "MNQ"]
mgc = [p for p in S if kind_of(p) == "single" and market_of(p) == "MGC"]
books_rows = "".join(row(p, i, dd_cols=True) for i, p in enumerate(book_list, 1))
combo_rows = "".join(row(p, i, dd_cols=True) for i, p in enumerate(combos, 1))
mnq_rows = "".join(row(p, i, dd_cols=True) for i, p in enumerate(mnq, 1))
mgc_rows = "".join(row(p, i, dd_cols=True) for i, p in enumerate(mgc, 1))
if COMBINED:
    print("combined books: K x{} dd1x ${:,.0f} net1x ${:,.0f}".format(COMBINED["mult"], COMBINED["dd1"], COMBINED["net1"]))
    print("combined books: net ${:,.0f} maxDD ${:,.0f} months {} RoDD {:.2f} RoDD/mo {} trades {:,} win {} PF {} avg/mo ${:,.0f} span {}..{}".format(
        COMBINED["net"], COMBINED["dd"], COMBINED["months"], COMBINED["rodd"], rodd_mo_pct(COMBINED["best"]["stats"]),
        COMBINED["n"], COMBINED["best"]["stats"]["Win"], COMBINED["best"]["stats"]["PF"], avg_monthly_profit(COMBINED), COMBINED["first"], COMBINED["last"]))
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
<title>Automated Futures Trading — AFT Trading Bots for Nasdaq, Gold, Dow, Russell &amp; S&amp;P Futures</title>
<meta name="description" content="Automated futures trading strategies for Nasdaq (MNQ), gold (MGC), Dow (MYM), Russell 2000 (M2K), S&amp;P 500 (MES) and silver (SIL) micro futures: backtest-verified algorithmic trading bots delivered as TradingView invite-only scripts, every trade published. Activated to your TradingView username within 24 hours.">
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
    <a class="btn btn-sm btn-discord" href="https://discord.gg/aft-traders" target="_blank" rel="noopener"><svg class="ic-discord" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.7 17.4c-3.2-.1-4.9-1.7-4.9-1.7.3-4 1.4-6.6 2.7-8.3C7.8 6.4 9.2 6 9.2 6l.5 1.1c1.5-.3 3.1-.3 4.6 0L14.8 6s1.4.4 2.7 1.4c1.3 1.7 2.4 4.3 2.7 8.3 0 0-1.7 1.6-4.9 1.7l-.8-1.1c-1.6.3-3.4.3-5 0z"/><circle cx="9.6" cy="12.6" r="1.15" fill="currentColor" stroke="none"/><circle cx="14.4" cy="12.6" r="1.15" fill="currentColor" stroke="none"/></svg><span>Discord</span></a>
    <details class="nav-mob">
      <summary aria-label="Menu"><span class="burger" aria-hidden="true"><i></i><i></i><i></i></span></summary>
      <nav class="nav-mob-panel" aria-label="Mobile">
        <a href="/">All strategies</a>
        <a href="/strategies/all-access.html">All-Access</a>
        <a href="/plan.html">Plan finder</a>
        <!-- DISCORD: community invite -->
        <a href="https://discord.gg/aft-traders" target="_blank" rel="noopener">Discord</a>
      </nav>
    </details>
  </div>
</header>

<main class="sx-main" id="main">
  <div class="sx-hero">
    <div class="sx-hero-copy">
      <h1 class="sx-hero-h1">Automated <span class="hl">Futures Trading</span></h1>
      <p class="sx-tag">Unmatched automated trading strategies for Nasdaq, gold, Dow, Russell and S&amp;P futures. Backtest-verified algorithmic trading bots that run on your own TradingView account, every trade published, nothing hidden.</p>
      <p class="sx-lede">{len(S)} automated futures trading strategies live today on MNQ and MGC, with Dow, Russell, S&amp;P and silver strategies in TradingView validation below, all delivered as TradingView invite-only scripts and live on your TradingView username within 24 hours. Return on drawdown is the number every strategy is ranked and priced on.</p>
      <p class="sx-cta">Pick a strategy below to see its Strategy Tester report, monthly calendars and every trade.</p>
      <p class="sx-note">Figures below are each strategy&rsquo;s best validated window, commissions and slippage modeled.
      The full record, good or ugly, is published on every specification page. Ranked by average monthly return
      on drawdown (RoDD/mo) &mdash; return on drawdown = net profit &divide; maximum drawdown over the window,
      shown per month of the record. Avg Monthly Profit = the window&rsquo;s closed-trade net profit divided by
      its months, at the shown multiplier. Win Rate and Profit Factor are the window&rsquo;s closed-trade figures.</p>
    </div>
    <div class="coverflow" aria-label="Flagship strategies">{cf_block()}</div>
  </div>

  {special_strip()}
  <p class="sx-ddnote">All strategies simulated based on a $10,000 or less drawdown.</p>

{table("The Books", books_rows, len(book_list), dd_cols=True, sec_id="books",
       lede="The whole-day engines. The first row is both books run together in one account: each book taken back to one multiple, the two curves merged, then sized to the largest whole multiplier that keeps the combined drawdown under $10,000 (never below &times;3); the combined drawdown is measured on the merged daily equity curve.")}

{table("Combo sets", combo_rows, len(combos), dd_cols=True, sec_id="combos",
       lede="Multi-strategy sets: two or three legs routed through one script.")}

{table("MNQ · Nasdaq futures", mnq_rows, len(mnq), dd_cols=True)}

{table("MGC · Gold futures", mgc_rows, len(mgc), dd_cols=True)}

{coming_soon_html()}

  <p class="sx-all"><!-- WHOP: replace with All-Access checkout link when it exists -->
  All {len(S)} strategies under one subscription: <a href="/strategies/all-access.html">All-Access — ${CAT["bundles"]["all_access"]["price"]} / mo</a>.
  {("(" + esc(CAT["bundles"]["all_access"]["prepay"]["line"]) + ".) ") if CAT["bundles"]["all_access"].get("prepay") else ""}Not sure where to start: <a href="/plan.html">the plan finder</a> ranks them against your drawdown budget.</p>


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
      <a class="foot-discord" href="https://discord.gg/aft-traders" target="_blank" rel="noopener"><svg class="ic-discord" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8.7 17.4c-3.2-.1-4.9-1.7-4.9-1.7.3-4 1.4-6.6 2.7-8.3C7.8 6.4 9.2 6 9.2 6l.5 1.1c1.5-.3 3.1-.3 4.6 0L14.8 6s1.4.4 2.7 1.4c1.3 1.7 2.4 4.3 2.7 8.3 0 0-1.7 1.6-4.9 1.7l-.8-1.1c-1.6.3-3.4.3-5 0z"/><circle cx="9.6" cy="12.6" r="1.15" fill="currentColor" stroke="none"/><circle cx="14.4" cy="12.6" r="1.15" fill="currentColor" stroke="none"/></svg><span>Discord</span></a>
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
print(f"index written: {len(book_list)} book rows + {len(combos)} combo rows + {len(mnq)} MNQ + {len(mgc)} MGC singles, effective {today}")
