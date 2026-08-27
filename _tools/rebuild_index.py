"""Rebuild index.html's catalog-driven sections from catalog2.json.
Splices: ticker, stats strip, hero lede, the whole #strategies section,
the #packages bundles, and finder price mentions. Static sections
(hero dial, why, finder structure, how, security, faq, footer) untouched."""
import json, os, re, sys, html, hashlib
from glyphs import glyph, emblem
_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(_HERE)
CAT = json.load(open(os.path.join(_HERE, "catalog2.json"), encoding="utf-8"))
S = CAT["strategies"]
WHOP_STORE = CAT.get("whop_store") or "/#packages"
WHOP_BY_SLUG = {s["slug"]: s.get("whop") for s in S}
def buy_href(p):
    return p.get("whop") or f"/strategies/{p['slug']}.html"
COMBINED_ALL = sum(s["price"] for s in S)   # struck bundle price, never a constant
COMBINED_TOP3 = sum(sorted((s["price"] for s in S), reverse=True)[:3])
B = CAT["books"]
BN = CAT["bundles"]

def esc(s): return html.escape(str(s), quote=False)
def num(v):
    s = str(v).replace("$", "").replace(",", "").replace("%", "")
    m = 1000 if s.endswith("k") else 1
    try: return float(s.rstrip("k")) * m
    except ValueError: return 0.0
def bs(p, k): return p["best"]["stats"].get(k, "—")
def is_hot(key, val):
    v = num(val)
    return {"RoDD": v >= 10, "PF": v >= 2.0, "Win": v >= 80, "Trades": v >= 1000, "Net": v >= 150000}.get(key, False)
def market_chips(meta):
    first = meta.split("·")[0].strip()
    out = ""
    for mkt in first.replace("+", " ").split():
        if mkt.isalpha() and mkt.isupper() and 1 < len(mkt) <= 4:
            out += f'<span class="chip chip-mkt">{mkt}</span>'
    return out or f'<span class="chip chip-mkt">{esc(first[:6])}</span>'

doc = open(os.path.join(BASE, "index.html"), encoding="utf-8").read()

# ── preserve hand-written blocks inside #strategies ─────────────
gl = re.search(r'(<div class="glossary">.*?)(?=\n\s*(?:<article|<div class="tier-head"|<div class="collections"|<div class="prelaunch"))', doc, re.S)
GLOSSARY = re.sub(r'(?:\s*<!--[^>]*-->)+\s*$', '', gl.group(1)).rstrip() if gl else ""
fn = re.search(r'(<div class="sec-footnote">.*?</div>)\s*\n', doc, re.S)
FOOTNOTE = fn.group(1) if fn else ""
assert GLOSSARY and FOOTNOTE, "glossary/footnote anchors missing"

ADD = lambda slug, name: (
    f'<input type="checkbox" id="add-{slug}" class="add-cb">'
    f'<label for="add-{slug}" class="add-btn add-btn-card"><span class="add-ico" aria-hidden="true"></span>'
    f'<span class="add-txt">Add</span><span class="sr-only"> {esc(name)} to selection</span></label>')
ACTCELL = lambda slug, name: (
    f'<td class="act-cell"><!-- WHOP: replace this product-page link with the Whop checkout link -->'
    f'<a class="btn btn-buy btn-row" href="{WHOP_BY_SLUG.get(slug) or ("/strategies/" + slug + ".html")}" rel="noopener">Get access</a>'
    f'<input type="checkbox" id="add-{slug}" class="add-cb">'
    f'<label for="add-{slug}" class="add-btn"><span class="add-ico" aria-hidden="true"></span>'
    f'<span class="add-txt">Add</span><span class="sr-only"> {esc(name)} to selection</span></label></td>')

# PRE-LAUNCH: no published products -> placeholder band instead of catalog
PRELAUNCH = not S

LEAD_KEYS = ["RoDD", "PF", "Win", "Net", "Trades"]
LEADERS = {} if PRELAUNCH else {k: max(S, key=lambda p: num(bs(p, k)))["slug"] for k in LEAD_KEYS}
def val_cls(p, k):
    v = bs(p, k)
    if k in LEAD_KEYS and LEADERS.get(k) == p["slug"]:
        return "lead"
    return "hot" if is_hot(k, v) else ""

# really low max drawdowns get medal tiers: gold <= $2k, neon green <= $5k
def dd_cls(v):
    n = num(v)
    return "dd-gold" if n <= 2000 else ("dd-neon" if n <= 5000 else "")

# per-strategy stat ranks across the whole catalog (1 = best) — used to pick
# each flagship's standout stat, the figure that makes it a flagship
RANK_KEYS = ["RoDD", "PF", "Win", "Net", "Trades", "Max DD"]
RANKS = {}
for _k in RANK_KEYS:
    order = sorted(S, key=lambda p: (num(bs(p, _k)) if _k != "Max DD" else -num(bs(p, _k))), reverse=True)
    for _i, _p in enumerate(order):
        RANKS[(_p["slug"], _k)] = _i + 1
STAR_PRIORITY = ["RoDD", "Net", "Win", "Max DD", "PF", "Trades"]
def star_key(p):
    best = min(RANK_KEYS, key=lambda k: (RANKS.get((p["slug"], k), 99), STAR_PRIORITY.index(k)))
    return best

srt = sorted(S, key=lambda x: -x["price"])
TIER1, TIER2, TIER3 = srt[:6], [x for x in srt[6:] if x["price"] >= 149], [x for x in srt[6:] if x["price"] < 149]
_D = {"slug": "tbd", "name": "TBD", "actual": "TBD", "meta": "TBD", "window": "TBD",
      "price": 0, "sep": ["TBD"], "legs": [],
      "best": {"label": "TBD", "stats": {k: "0" for k in
               ["RoDD", "PF", "Win", "Net", "Max DD", "Trades", "$/trade", "Months", "RoDD/mo"]}},
      "full": {"label": "TBD", "stats": {}}}
if PRELAUNCH:
    TIER1 = TIER2 = TIER3 = [_D]   # placeholder-evaluated, then overridden

# ── real equity sparkline, precomputed (zero-JS rule: never a chart lib) ──
def load_trades(slug):
    p = os.path.join(_HERE, "trades", slug + ".json")
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))

SPARK_W, SPARK_H = 1200.0, 300.0

def sparkline(slug, cls="fspark", pfx="fsg", maxpts=0):
    """Full-bleed equity curve for a flagship card. preserveAspectRatio is
    'none' so it stretches edge to edge - safe here because the sparkline
    carries no text (unlike the product-page chart, which must not distort)."""
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
    """Net normalised to a fixed drawdown so the five are comparable."""
    return num(bs(p, "RoDD")) * BASE_DD

def gain_figure(p):
    """The published best-window net, shown as a gain. Traceable: the window
    is printed directly beneath it on the card."""
    tr = load_trades(p["slug"])
    v = (tr or {}).get("best", {}).get("net")
    if v is None:
        return esc(bs(p, "Net")), ""
    return f"+${v:,.0f}", esc(p.get("window", ""))

# ── flagship cards ──────────────────────────────────────────────
def card_star(p):
    """Corner stat for a chart card. Net is excluded: the green gain figure at
    the bottom of the card already IS the net, so showing it twice wastes the
    corner. RoDD wins by default; a product whose real strength is drawdown or
    win rate shows that instead."""
    keys = [k for k in RANK_KEYS if k != "Net"]
    return min(keys, key=lambda k: (RANKS.get((p["slug"], k), 99), STAR_PRIORITY.index(k)))

def card_star_tag(p):
    k = card_star(p)
    rk = RANKS.get((p["slug"], k), 99)
    lab = "MAX DD" if k == "Max DD" else k.upper()
    return f"#{rk} {lab}" if rk <= 3 else lab

def fcard(p):
    stats = ""
    star = star_key(p)
    for k, lab in [("RoDD", "RoDD"), ("PF", "PF"), ("Win", "Win"), ("Net", "Net"), ("Max DD", "Max DD"), ("Trades", "n")]:
        v = bs(p, k)
        cls = [c for c in (val_cls(p, k),) if c]
        if k == "Max DD" and dd_cls(v): cls.append(dd_cls(v))
        hot = f' class="{" ".join(cls)}"' if cls else ""
        tile_cls = "fstat fstat-star" if k == star else "fstat"
        if k == star:
            rk = RANKS.get((p["slug"], k), 99)
            lab_tag = f"#{rk} {'MAX DD' if k == 'Max DD' else k.upper()}" if rk <= 3 else "SIGNATURE"
            tag = f'<i class="star-tag">{lab_tag}</i>'
        else:
            tag = ""
        stats += f'<div class="{tile_cls}"><b{hot}>{esc(v)}</b><span>{lab}</span>{tag}</div>'
    gain, gwin = gain_figure(p)
    fstats = (p.get("full") or {}).get("stats", {})
    full_line = ""
    if fstats:
        full_line = ('<p class="ffull"><span>Full record</span> '
                     + ' &middot; '.join(f'{fstats.get(k, "&mdash;")} {lab}'
                                         for k, lab in [("RoDD", "RoDD"), ("PF", "PF"),
                                                        ("Max DD", "max DD"), ("Trades", "trades")])
                     + '</p>')
    gainrow = (f'<div class="fgainrow"><b>${baseline(p):,.0f}</b>'
               f'<span>on a ${BASE_DD:,} drawdown &middot; best window</span></div>')
    return f"""<article class="fcard fc-{p['slug']}">
          <div class="fcard-top">
            <span class="fglyph" aria-hidden="true">{glyph(p['slug'], 'glyph g-flag')}</span>
            <div class="fcard-id">
              <h4><a class="sys-link" href="/strategies/{p['slug']}.html">{esc(p['name'])}</a></h4>
              <div class="fline">
                <span class="card-real">{esc(p['actual'])}</span>
                <span class="fline-sep" aria-hidden="true">&middot;</span>
                <span class="fmeta">{market_chips(p['meta'])}<span class="chip chip-verified">VERIFIED</span></span>
              </div>
            </div>
            <div class="fhero"><b>{esc(bs(p,'RoDD'))}&times;</b><span>RoDD &middot; best window</span></div>
          </div>
          <p class="desc">{esc(p['sep'][0]) if p['sep'] else ''}</p>
          {gainrow}
          <div class="fstats">{stats}</div>
          {full_line}
          <div class="price-row">
            <div class="price"><span class="now">${p['price']}</span><span class="per">/MO</span></div>
          </div>
          {ADD(p['slug'], p['name'])}
          <div class="cta-row">
            <a class="btn" href="/strategies/{p['slug']}.html">View full data<svg class="ic-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6" vector-effect="non-scaling-stroke"/></svg></a>
            <!-- WHOP: replace this product-page link with the Whop checkout link -->
            <a class="btn btn-buy" href="{buy_href(p)}" rel="noopener">Get access</a>
          </div>
          <p class="mini-guar">7-day money-back &middot; first month refunded if the signals lose &middot; cancel anytime</p>
        </article>"""

# ── screener tables ─────────────────────────────────────────────
def trow(p):
    cells = ""
    for k in ["RoDD", "PF", "Win", "Net", "Max DD", "Trades"]:
        v = bs(p, k)
        cls = []
        if k == "RoDD": cls.append("pf")
        vc = val_cls(p, k)
        if vc: cls.append(vc)
        if k == "Max DD":
            dc = dd_cls(v)
            if dc: cls.append(dc)
        c = f' class="{" ".join(cls)}"' if cls else ""
        cells += f'<td{c}>{esc(v)}</td>'
    return f"""<tr>
              <th scope="row"><div class="sys"><span class="gcell" aria-hidden="true">{glyph(p['slug'], 'glyph g-row')}</span><div class="sys-txt"><div class="sys-name-row"><a class="sys-link" href="/strategies/{p['slug']}.html"><span class="sys-name">{esc(p['name'])}</span></a><span class="sys-real">{esc(p['actual'])}</span>{market_chips(p['meta'])}<span class="chip chip-verified">VERIFIED</span></div><span class="sys-desc">{esc(p['sep'][0][:110]) if p['sep'] else ''}</span></div></div></th>
              {cells}
              <td class="price-cell">${p['price']}<span class="per">/mo</span></td>
              {ACTCELL(p['slug'], p['name'])}
            </tr>"""

def table(tier, label, items, anchor):
    rows = "\n            ".join(trow(p) for p in items)
    return f"""<div class="tier-head" id="{anchor}">
        <span class="tier-tag">{tier}</span>
        <h3>{label}</h3>
        <span class="note">${min((p['price'] for p in items), default=0)}&ndash;${max((p['price'] for p in items), default=0)}/mo &middot; {len(items)} systems</span>
      </div>

      <p class="scroll-hint" aria-hidden="true">scroll &rarr;</p>
      <!-- a11y: unconditional tabindex is an accepted trade-off on this zero-JS page -->
      <div class="screener" tabindex="0" role="region" aria-label="{label} table, scrolls horizontally">
        <table class="stable">
          <caption class="sr-only">{label}: validated best-window stats and pricing</caption>
          <thead>
            <tr>
              <th scope="col">System</th>
              <th scope="col"><abbr title="Return over max drawdown">RoDD</abbr></th>
              <th scope="col">PF</th>
              <th scope="col">Win</th>
              <th scope="col">Net</th>
              <th scope="col">Max DD</th>
              <th scope="col">n</th>
              <th scope="col">Price</th>
              <th scope="col"><span class="sr-only">Purchase or add to selection</span></th>
            </tr>
          </thead>
          <tbody>
            {rows}
          </tbody>
        </table>
      </div>"""

# ── collections ─────────────────────────────────────────────────
def coll(title, rows, extra=""):
    lis = "".join(
        f'<li><a class="sys-link" href="/strategies/{s}.html"><span class="col-name">{esc(n)}</span></a><span class="col-stat">{esc(v)}</span></li>'
        for s, n, v in rows)
    return f"""<div class="collection{extra and ' ' + extra}">
          <div class="col-title">{title}</div>
          <ul>{lis}</ul>
        </div>"""

def top_by(key, fmt, n=4, rev=True):
    xs = sorted(S, key=lambda p: -num(bs(p, key)) if rev else num(bs(p, key)))[:n]
    return [(p["slug"], p["name"], fmt(p)) for p in xs]

collections = f"""<div class="tier-head">
        <span class="tier-tag">BROWSE</span>
        <h3>By edge</h3>
      </div>

      <div class="collections" id="edge">
        {coll("Best value · RoDD", top_by("RoDD", lambda p: f"{bs(p,'RoDD')}× · n={bs(p,'Trades')}"), extra="col-value")}
        {coll("High win rate", top_by("Win", lambda p: bs(p, "Win")))}
        {coll("High return", top_by("Net", lambda p: bs(p, "Net")))}
        {coll("High frequency", top_by("Trades", lambda p: f"n={bs(p,'Trades')}"))}
      </div>"""

# ── cart ────────────────────────────────────────────────────────
cart_lines = "".join(
    f'<li class="cl cl-{p["slug"]}"><span class="cl-name">{esc(p["name"])}</span><span class="cl-price">${p["price"]}</span></li>'
    for p in S)
cart = f"""<!-- ── selection cart: pure CSS (counters + :has), zero JS ─────────
           Counters accumulate from the checkboxes above, so this block must
           stay the LAST child of #strategies. Fixed-positioned for display. -->
      <input type="checkbox" id="cart-collapse" class="cart-cb">
      <aside class="cart" aria-label="Your selection" aria-live="polite">
        <div class="cart-top">
          <span class="cart-title">Selection</span>
          <span class="cart-count" aria-hidden="true"></span>
          <label for="cart-collapse" class="cart-toggle"><span class="sr-only">Collapse or expand your selection</span><span class="cart-chev" aria-hidden="true"></span></label>
        </div>
        <ul class="cart-lines">{cart_lines}</ul>
        <div class="cart-foot">
          <div class="cart-total"><span class="cart-tlabel">Total</span><span class="cart-sum"></span><span class="cart-per">/mo</span></div>
          <p class="cart-hint">Want the catalog? <a href="/strategies/all-access.html">All-Access is $999/mo</a> &mdash; combined list ${COMBINED_ALL:,}.</p>
          <a class="btn btn-buy cart-go" href="#packages">Compare bundles</a>
          <span class="cart-note">Selections are local to this page &mdash; nothing is stored or sent.</span>
        </div>
      </aside>"""

# ── assemble #strategies ────────────────────────────────────────
strategies = f"""<section id="strategies">
    <div class="wrap">
      <div class="sec-head sec-head-dial">
        <span class="idx">01 /</span>
        <h2>Strategies</h2>
        <!-- session rotation dial — purely decorative; no numbers, no performance implication --> <div class="dial-wrap sec-dial" aria-hidden="true"> <svg class="dial" viewBox="0 0 420 420" xmlns="http://www.w3.org/2000/svg" focusable="false"> <!-- outer hairline ring --> <circle class="dial-outer" cx="210" cy="210" r="164" fill="none" stroke="#2A423E" stroke-width="1"/> <!-- fine tick marks: dashed-stroke circle --> <circle class="dial-tickring" cx="210" cy="210" r="152" fill="none" stroke="#2A423E" stroke-width="7" stroke-dasharray="1.5 8.45"/> <!-- session handoff: four arc segments (dasharray quarters), mint at stepped opacities --> <circle class="dial-arc dial-arc-a" cx="210" cy="210" r="118" fill="none" stroke="#56C8A2" stroke-width="2" stroke-dasharray="172 570" stroke-opacity=".9" transform="rotate(3.3 210 210)"/> <circle class="dial-arc dial-arc-b" cx="210" cy="210" r="118" fill="none" stroke="#56C8A2" stroke-width="2" stroke-dasharray="172 570" stroke-opacity=".62" transform="rotate(93.3 210 210)"/> <circle class="dial-arc dial-arc-c" cx="210" cy="210" r="118" fill="none" stroke="#56C8A2" stroke-width="2" stroke-dasharray="172 570" stroke-opacity=".42" transform="rotate(183.3 210 210)"/> <circle class="dial-arc dial-arc-d" cx="210" cy="210" r="118" fill="none" stroke="#56C8A2" stroke-width="2" stroke-dasharray="172 570" stroke-opacity=".26" transform="rotate(273.3 210 210)"/> <!-- session labels --> <text class="dial-label" x="210" y="30" text-anchor="middle" fill="#738D85">SYDNEY</text> <text class="dial-label" x="210" y="30" text-anchor="middle" fill="#738D85" transform="rotate(90 210 210)">SHANGHAI</text> <text class="dial-label" x="210" y="398" text-anchor="middle" fill="#738D85">FRANKFURT</text> <text class="dial-label" x="210" y="30" text-anchor="middle" fill="#738D85" transform="rotate(-90 210 210)">NEW YORK</text> <!-- sweep hand --> <g class="dial-hand"> <line x1="210" y1="210" x2="210" y2="74" fill="none" stroke="#56C8A2" stroke-width="1.5"/> <circle class="dial-hub" cx="210" cy="210" r="4.5" fill="#56C8A2"/> </g> </svg> </div>
      </div>

      {GLOSSARY}

      {collections}

      <div class="tier-head">
        <span class="tier-tag">TIER 1</span>
        <h3>Flagships</h3>
        <span class="note">${TIER1[-1]['price']}&ndash;${TIER1[0]['price']}/mo &middot; {len(TIER1)} systems</span>
      </div>

      <div class="flagships" id="flagships">

        {chr(10).join(fcard(p) for p in TIER1)}

      </div>

      {table("TIER 2", "Core systems", TIER2, "tier-2") if TIER2 and not PRELAUNCH else '<div id="tier-2"></div>'}

      {table("TIER 3", "Session specialists", TIER3, "tier-3") if TIER3 and not PRELAUNCH else '<div id="tier-3"></div>'}

      {FOOTNOTE}

      {cart}

    </div>
  </section>"""


# ── PRE-LAUNCH overrides: keep every template, publish a landing ────
if PRELAUNCH:
    slots = "".join(
        f'<li class="slot"><span class="slot-n">{i:02d}</span>'
        f'<span class="slot-lab">FLAGSHIP {i:02d}</span>'
        f'<span class="slot-sub">in validation</span></li>'
        for i in range(1, 6))
    strategies = f"""<section id="strategies">
    <div class="wrap">
      <div class="sec-head sec-head-dial">
        <span class="idx">01 /</span>
        <h2>Strategies</h2>
        <!-- session rotation dial — purely decorative; no numbers, no performance implication --> <div class="dial-wrap sec-dial" aria-hidden="true"> <svg class="dial" viewBox="0 0 420 420" xmlns="http://www.w3.org/2000/svg" focusable="false"> <!-- outer hairline ring --> <circle class="dial-outer" cx="210" cy="210" r="164" fill="none" stroke="#2A423E" stroke-width="1"/> <!-- fine tick marks: dashed-stroke circle --> <circle class="dial-tickring" cx="210" cy="210" r="152" fill="none" stroke="#2A423E" stroke-width="7" stroke-dasharray="1.5 8.45"/> <!-- session handoff: four arc segments (dasharray quarters), mint at stepped opacities --> <circle class="dial-arc dial-arc-a" cx="210" cy="210" r="118" fill="none" stroke="#56C8A2" stroke-width="2" stroke-dasharray="172 570" stroke-opacity=".9" transform="rotate(3.3 210 210)"/> <circle class="dial-arc dial-arc-b" cx="210" cy="210" r="118" fill="none" stroke="#56C8A2" stroke-width="2" stroke-dasharray="172 570" stroke-opacity=".62" transform="rotate(93.3 210 210)"/> <circle class="dial-arc dial-arc-c" cx="210" cy="210" r="118" fill="none" stroke="#56C8A2" stroke-width="2" stroke-dasharray="172 570" stroke-opacity=".42" transform="rotate(183.3 210 210)"/> <circle class="dial-arc dial-arc-d" cx="210" cy="210" r="118" fill="none" stroke="#56C8A2" stroke-width="2" stroke-dasharray="172 570" stroke-opacity=".26" transform="rotate(273.3 210 210)"/> <!-- session labels --> <text class="dial-label" x="210" y="30" text-anchor="middle" fill="#738D85">SYDNEY</text> <text class="dial-label" x="210" y="30" text-anchor="middle" fill="#738D85" transform="rotate(90 210 210)">SHANGHAI</text> <text class="dial-label" x="210" y="398" text-anchor="middle" fill="#738D85">FRANKFURT</text> <text class="dial-label" x="210" y="30" text-anchor="middle" fill="#738D85" transform="rotate(-90 210 210)">NEW YORK</text> <!-- sweep hand --> <g class="dial-hand"> <line x1="210" y1="210" x2="210" y2="74" fill="none" stroke="#56C8A2" stroke-width="1.5"/> <circle class="dial-hub" cx="210" cy="210" r="4.5" fill="#56C8A2"/> </g> </svg> </div>
      </div>

      {GLOSSARY}

      <div class="prelaunch" id="flagships">
        <span class="pl-tag">NEW LINEUP LOADING</span>
        <h3>The catalog is being rebuilt from scratch.</h3>
        <p>Every system that ships here goes through the same gate: validated runs,
        commissions and slippage modeled, both windows published, priced by the same
        RoDD formula. The previous catalog is retired; the first five flagships land
        as they clear validation.</p>
        <ul class="pl-slots" id="tier-2">{slots}</ul>
        <div class="pl-ctas" id="tier-3">
          <!-- DISCORD: community invite -->
          <a class="btn btn-buy" href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener">Get told the day they land</a>
          <a class="btn" href="/#how">How access will work</a>
        </div>
        <div id="edge"></div>
      </div>

      {FOOTNOTE}
    </div>
  </section>"""
    packages_prelaunch = f"""<section id="packages">
    <div class="wrap">
      <div class="sec-head">
        <span class="idx">02 /</span>
        <h2>Bundles</h2>
      </div>
      <div class="prelaunch" id="books">
        <span class="pl-tag">PRICING HOLDS</span>
        <h3>Bundles come back the day the catalog does.</h3>
        <p>The structure is already set &mdash; a Starter trio, Pick&#8209;3, All&#8209;Access,
        and the in&#8209;house Books &mdash; and every bundle will show its combined solo
        worth struck through, same as before. Numbers publish when the systems do.</p>
      </div>
    </div>
  </section>"""
    cf_panes_override = "".join(
        f'<div class="cf-pane"><a class="cf-link" href="/#strategies">'
        f'<b class="cf-name">{"FLAGSHIP %02d" % i if i <= 5 else "MORE"}</b>'
        f'<span class="cf-stat">{"IN VALIDATION" if i <= 5 else "AFTER THE TOP FIVE"}</span></a>'
        f'<label class="cf-pick" for="cf-{i}"><span class="sr-only">Bring slot {i} to the front</span></label></div>'
        for i in range(1, 6))

doc = re.sub(r'<section id="strategies">.*?</section>', strategies, doc, count=1, flags=re.S)

# ── bundles section ─────────────────────────────────────────────
BOOK_SKIN = {"the-midas": "bk-midas", "the-continuum": "bk-continuum",
             "the-daylight": "bk-daylight", "the-ledger": "bk-vault"}
BOOK_EPITHET = {"the-midas": "Everything it touches", "the-continuum": "Around the clock",
                "the-daylight": "One session, settled", "the-ledger": "Validated legs only"}
book_lis = "".join(
    f'<li class="bookcard {BOOK_SKIN[b["slug"]]}">{emblem(b["slug"])}'
    f'<a class="sys-link bk-name" href="/strategies/{b["slug"]}.html">{esc(b["name"])}</a>'
    f'<span class="bk-epithet">{esc(BOOK_EPITHET[b["slug"]])}</span>'
    f'<span class="bk-int">{esc(b["actual"]).upper()}</span>'
    f'<span class="bk-price">${b["price"]:,}<small>/MO SOLO</small></span></li>'
    for b in B)
inc_check = ('<svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg>')
packages = f"""<section id="packages">
    <div class="wrap">
      <div class="sec-head">
        <span class="idx">02 /</span>
        <h2>Bundles</h2>
      </div>

      <article class="pack pack-books" id="books">
        <div class="books-head">
          <h3><a class="sys-link" href="/strategies/the-books.html">The Books</a></h3>
          <span class="chip chip-mkt">IN-HOUSE ENGINES</span>
        </div>
        <p class="sub">The four engines we run ourselves &mdash; multi-leg routers, live-validated, both windows published. Sold separately from ${min((b['price'] for b in B), default=0):,}/mo; all four together under the price of any two.</p>
        <ul class="bookdeck">{book_lis}</ul>
        <div class="books-foot">
          <div class="amount"><s class="was">${BN['books_all']['combined']:,}<span class="sr-only"> combined solo price,</span></s>${BN['books_all']['price']:,}<small>/mo</small></div>
          <div class="books-ctas">
            <a class="btn" href="/strategies/the-books.html">View details<svg class="ic-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 7h10v10" vector-effect="non-scaling-stroke"/><path d="M7 17 17 7" vector-effect="non-scaling-stroke"/></svg></a>
            <!-- WHOP: replace this product-page link with the Whop checkout link -->
            <a class="btn btn-buy" href="/strategies/the-books.html" rel="noopener">Get the books</a>
          </div>
        </div>
      </article>

      <div class="packs-3">

        <div class="pack pack-starter">
          <span class="badge-special">STARTER SPECIAL</span>
          <h3><a class="sys-link" href="/strategies/the-starter.html">The Starter</a></h3>
          <div class="amount"><s class="was">${BN['starter']['combined']}<span class="sr-only"> combined solo price,</span></s>${BN['starter']['price']}<small>/mo</small></div>
          <p class="sub">Three structure systems, one price. The entry point to the catalog.</p>
          <ul>
            {"".join(f'<li>{inc_check}<span>{esc(next((s for s in S if s["slug"] == sl), _D)["name"])} &middot; {esc(next((s for s in S if s["slug"] == sl), _D)["actual"])}</span></li>' for sl in BN['starter']['slugs'])}
          </ul>
          <!-- WHOP: replace this product-page link with the Whop checkout link -->
          <a class="btn btn-buy" href="/strategies/the-starter.html" rel="noopener">Get the starter</a>
        </div>

        <div class="pack popular">
          <span class="flag">BEST VALUE</span>
          <h3><a class="sys-link" href="/strategies/all-access.html">All-Access</a></h3>
          <div class="amount"><s class="was">${COMBINED_ALL:,}<span class="sr-only"> combined list price,</span></s>$999<small>/mo</small></div>
          <p class="sub">Every validated strategy in the catalog.</p>
          <ul>
            <li>{inc_check}<span>All {len(S)} live-validated systems, every tier included</span></li>
            <li>{inc_check}<span>New systems included as they clear validation</span></li>
            <li>{inc_check}<span>TradingView invite-only scripts, activated within 24h</span></li>
            <li class="li-note"><span>The Books not included &mdash; separate premium tier</span></li>
          </ul>
          <!-- WHOP: replace this product-page link with the Whop checkout link -->
          <a class="btn btn-buy" href="/strategies/all-access.html" rel="noopener">Get all-access</a>
        </div>


      </div>

      <p class="banner">Annual on anything = <b>2 months free</b></p>

      <!-- starter special pop-up: pure CSS, dismissible, bottom-left -->
      <input type="checkbox" id="pop-dismiss" class="pop-cb">
      <aside class="special-pop" aria-label="Starter special offer">
        <label for="pop-dismiss" class="pop-close"><span class="sr-only">Dismiss offer</span><span class="pop-x" aria-hidden="true"></span></label>
        <span class="badge-special">STARTER SPECIAL</span>
        <p class="pop-line"><b>3 systems &middot; ${BN['starter']['price']}/mo</b></p>
        <p class="pop-sub">{" + ".join(esc(next((s for s in S if s["slug"] == sl), _D)["name"]) for sl in BN['starter']['slugs'])} &mdash; the lowest published drawdowns in the value tiers. Worth <s class="was">${BN['starter']['combined']}</s> solo.</p>
        <!-- WHOP: replace this product-page link with the Whop checkout link -->
        <a class="btn btn-buy pop-go" href="/strategies/the-starter.html" rel="noopener">Get 3 for ${BN['starter']['price']}</a>
      </aside>
    </div>
  </section>"""

BOOKS_PENDING = (not B) and (not PRELAUNCH)
if BOOKS_PENDING:
    packages = f"""<section id="packages">
    <div class="wrap">
      <div class="sec-head">
        <span class="idx">02 /</span>
        <h2>Bundles</h2>
      </div>
      <div class="packs-1">

        <div class="pack popular">
          <span class="flag">BEST VALUE</span>
          <h3><a class="sys-link" href="/strategies/all-access.html">All-Access</a></h3>
          <div class="amount"><s class="was">${COMBINED_ALL:,}<span class="sr-only"> combined list price,</span></s>$999<small>/mo</small></div>
          <p class="sub">Every published system under one subscription.</p>
          <ul>
            <li>{inc_check}<span>All {len(S)} live-validated systems included</span></li>
            <li>{inc_check}<span>New systems included as they clear validation</span></li>
            <li>{inc_check}<span>TradingView invite-only scripts, activated within 24h</span></li>
          </ul>
          <!-- WHOP: replace this product-page link with the Whop checkout link -->
          <a class="btn btn-buy" href="/strategies/all-access.html" rel="noopener">Get All-Access</a>
          <p class="mini-guar">7-day money-back &middot; first month refunded if the signals lose &middot; cancel anytime</p>
        </div>


      </div>
      <div class="prelaunch" id="books">
        <span class="pl-tag">IN VALIDATION</span>
        <h3>The Books are next.</h3>
        <p>The five flagships shipped first. The multi&#8209;leg Books &mdash; the in-house engines we
        run ourselves &mdash; publish when they clear the same validation gate, with both windows
        shown like everything else here.</p>
      </div>
    </div>
  </section>"""
if PRELAUNCH:
    packages = packages_prelaunch
doc = re.sub(r'<section id="packages">.*?</section>', packages, doc, count=1, flags=re.S)

# ── ticker, stats strip, hero lede, finder prices, counts ───────
tick_names = [] if PRELAUNCH else [(p["name"].upper()) for p in sorted(S, key=lambda x: -num(bs(x, "RoDD")))[:7]]
tick = "".join(f"<span>{esc(n)} · VERIFIED</span>" for n in tick_names)
if PRELAUNCH:
    half = ("<span>NEW LINEUP IN VALIDATION</span>"
            "<span>SESSION: SYDNEY → SHANGHAI → FRANKFURT → NEW YORK</span>"
            "<span>TOP FIVE FLAGSHIPS FIRST</span>"
            "<span>DELIVERY: TRADINGVIEW INVITE-ONLY · ACTIVATED WITHIN 24H</span>")
else:
    # markets and book count come from the catalog, never a hardcoded list
    _seen = []
    for _p in S + B:
        _m = _p["meta"].split("·")[0].strip().split()[0].strip()
        if _m and _m not in _seen: _seen.append(_m)
    MARKETS = " · ".join(_seen)
    MARKETS_TIGHT = "·".join(_seen)
    MARKETS_PROSE = (", ".join(_seen[:-1]) + " and " + _seen[-1]) if len(_seen) > 1 else (_seen[0] if _seen else "")
    _books = f"{len(B)} BOOKS" if B else "BOOKS IN VALIDATION"
    half = (f"<span>{len(S)} SYSTEMS · {_books}</span>"
        f"<span>SESSION: SYDNEY → SHANGHAI → FRANKFURT → NEW YORK</span>"
        + tick +
        f"<span>MARKETS: {MARKETS}</span>"
        f"<span>DELIVERY: TRADINGVIEW INVITE-ONLY · ACTIVATED WITHIN 24H</span>")
doc = re.sub(r'(<div class="ticker-track">\s*).*?(\s*</div>\s*</div>\s*</div>)',
             lambda m: m.group(1) + half + half + m.group(2), doc, count=1, flags=re.S)

stats_strip = f"""<ul class="stats wrap">
    <li><b>{'5' if PRELAUNCH else len(S) + len(B)}</b><span>{'Flagship slots reserved' if PRELAUNCH else 'Validated products'}</span></li>
    <li><b>{'5' if PRELAUNCH else len(_seen)}</b><span class="oneline">{'MNQ·NQ·MGC·SI·ES' if PRELAUNCH else MARKETS_TIGHT}</span></li>
    <li><b>2&times;</b><span>Windows published</span></li>
    <li><b>24h</b><span>Activation window</span></li>
  </ul>"""
doc = re.sub(r'<ul class="stats wrap">.*?</ul>', stats_strip, doc, count=1, flags=re.S)

LEDE = ("""<p class="lede">
          The catalog is being rebuilt. Every system that publishes here is live-validated
          &mdash; best window and full 2024+ window, both shown, commissions and slippage modeled.
          The top five flagships land first; nothing is listed before it clears the gate.
          TradingView invite-only scripts, activated within 24h. Checkout runs through Whop.
        </p>""" if PRELAUNCH else f"""<p class="lede">""")
doc = re.sub(r'<p class="lede">.*?</p>',
    LEDE if PRELAUNCH else f"""<p class="lede">
          {len(S)} session strategies for {MARKETS_PROSE} futures. Every number replayed from the
          validated trade record &mdash; both windows published.
        </p>""", doc, count=1, flags=re.S)

for old, new in [("$4,999", "$2,999"), ("all four in-house engines · each also solo at $1,499/mo", f"all four in-house engines · solo from ${min((b['price'] for b in B), default=0)}/mo"),
                 ("each also solo at $1,499/mo", f"solo from ${min((b['price'] for b in B), default=0)}/mo"),
                 ("Start with one system from $59/mo", f"Start with one system from ${min((p['price'] for p in S), default=0)}/mo"),
                 ("from $59/mo", f"from ${min((p['price'] for p in S), default=0)}/mo")]:
    doc = doc.replace(old, new)

cf_radios = ('<input class="cf-r" type="radio" name="cf-sel" id="cf-0" checked>'
             + "".join(f'<input class="cf-r" type="radio" name="cf-sel" id="cf-{i+1}">'
                       for i in range(len(TIER1))))
cf_panes = cf_panes_override if PRELAUNCH else "".join(
    f'<div class="cf-pane fc-{p["slug"]}">'
    f'<a class="cf-link" href="/strategies/{p["slug"]}.html">'
    + sparkline(p["slug"], cls="cf-spark", pfx="cf-sg", maxpts=64)
    + f'<span class="cf-glyphwrap" aria-hidden="true">{glyph(p["slug"], "glyph cf-glyph")}</span>'
    + f'<span class="cf-star"><b>{esc(bs(p, card_star(p)))}</b><i>{card_star_tag(p)}</i></span>'
    + f'<span class="cf-foot"><span class="cf-titlerow"><b class="cf-name">{esc(p["name"])}</b>'
    + f'<span class="cf-price">${p["price"]}<small>/mo</small></span></span>'
    + f'<span class="cf-gain">${baseline(p):,.0f}</span>'
    + f'<span class="cf-win">on a ${BASE_DD:,} drawdown &middot; best window</span></span></a>'
    f'<label class="cf-pick" for="cf-{i+1}"><span class="sr-only">Bring {esc(p["name"])} to the front</span></label>'
    f'</div>'
    for i, p in enumerate(TIER1))
cf_dots_prelaunch = "".join(
    f'<label class="cf-dot" for="cf-{i}"><span class="sr-only">Flagship slot {i}</span></label>'
    for i in range(1, 7))
cf_dots = cf_dots_prelaunch if PRELAUNCH else "".join(
    f'<label class="cf-dot fc-{p["slug"]}" for="cf-{i+1}"><span class="sr-only">{esc(p["name"])}</span></label>'
    for i, p in enumerate(TIER1))
cf_html = (cf_radios + f'<div class="cf-stage">{cf_panes}</div>'
           f'<div class="cf-dots">{cf_dots}'
           '<label class="cf-play" for="cf-0"><span class="cf-play-ico" aria-hidden="true"></span>'
           '<span class="sr-only">Resume the automatic rotation</span></label></div>')
doc = re.sub(r"(<!-- CFGEN -->).*?(<!-- /CFGEN -->)",
             lambda m: m.group(1) + cf_html + m.group(2), doc, count=1, flags=re.S)

open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(doc)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print(f"index rebuilt: {len(TIER1)} flagships, {len(TIER2)}+{len(TIER3)} table rows, cart {len(S)} lines")

# ── cart CSS rules (CARTGEN region in main.css) ─────────────────
css_path = os.path.join(BASE, "assets", "main.css")
css = open(css_path, encoding="utf-8").read()
NL = chr(10)
incs = NL.join(
    f"#add-{p['slug']}:checked + .add-btn {{ counter-increment: cart 1 total {p['price']}; }}"
    for p in S)
reveals = ("," + NL).join(f"#strategies:has(#add-{p['slug']}:checked) .cl-{p['slug']}" for p in S)
if PRELAUNCH:
    S_rules = []
block = ("/* CARTGEN:rules " + chr(8212) + " generated from catalog2.json; do not hand-edit */" + NL
         + incs + NL
         + reveals + " {" + NL
         + "  display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3);" + NL
         + "  padding: var(--sp-2) var(--sp-4); border-bottom: 1px solid var(--line);" + NL + "}" + NL)
css = re.sub(r"/\* CARTGEN:rules.*$", lambda m: block, css, flags=re.S)
open(css_path, "w", encoding="utf-8").write(css)
print("CARTGEN css region regenerated:", len(S), "increment rules")
