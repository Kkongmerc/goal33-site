"""Rebuild index.html's catalog-driven sections from catalog2.json.
Splices: ticker, stats strip, hero lede, the whole #strategies section,
the #packages bundles, and finder price mentions. Static sections
(hero dial, why, finder structure, how, security, faq, footer) untouched."""
import json, os, re, sys, html, hashlib
_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(_HERE)
CAT = json.load(open(os.path.join(_HERE, "catalog2.json"), encoding="utf-8"))
S = CAT["strategies"]
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
gl = re.search(r'(<div class="glossary">.*?)(?=\n\s*(?:<article|<div class="tier-head"|<div class="collections"))', doc, re.S)
GLOSSARY = re.sub(r'(?:\s*<!--[^>]*-->)+\s*$', '', gl.group(1)).rstrip() if gl else ""
fn = re.search(r'(<div class="sec-footnote">.*?</div>)\s*\n', doc, re.S)
FOOTNOTE = fn.group(1) if fn else ""
assert GLOSSARY and FOOTNOTE, "glossary/footnote anchors missing"

ADD = lambda slug, name: (
    f'<input type="checkbox" id="add-{slug}" class="add-cb">'
    f'<label for="add-{slug}" class="add-btn add-btn-card"><span class="add-ico" aria-hidden="true"></span>'
    f'<span class="add-txt">Add</span><span class="sr-only"> {esc(name)} to selection</span></label>')
ADDCELL = lambda slug, name: (
    f'<td class="add-cell"><input type="checkbox" id="add-{slug}" class="add-cb">'
    f'<label for="add-{slug}" class="add-btn"><span class="add-ico" aria-hidden="true"></span>'
    f'<span class="add-txt">Add</span><span class="sr-only"> {esc(name)} to selection</span></label></td>')

srt = sorted(S, key=lambda x: -x["price"])
TIER1, TIER2, TIER3 = srt[:6], [x for x in srt[6:] if x["price"] >= 149], [x for x in srt[6:] if x["price"] < 149]

# ── flagship cards ──────────────────────────────────────────────
def fcard(p):
    stats = ""
    for k, lab in [("RoDD", "RoDD"), ("PF", "PF"), ("Win", "Win"), ("Net", "Net"), ("Max DD", "Max DD"), ("Trades", "n")]:
        v = bs(p, k)
        hot = ' class="hot"' if is_hot(k, v) else ""
        stats += f'<div class="fstat"><b{hot}>{esc(v)}</b><span>{lab}</span></div>'
    return f"""<article class="fcard">
          <div class="fcard-top">
            <div class="fcard-id">
              <h4><a class="sys-link" href="/strategies/{p['slug']}.html">{esc(p['name'])}</a></h4>
          <div class="card-real">{esc(p['actual'])}</div>
              <div class="fmeta">{market_chips(p['meta'])}<span class="chip chip-verified">VERIFIED</span></div>
              <span class="fmeta-note">{esc(p['window'])}</span>
            </div>
            <div class="fhero"><b>{esc(bs(p,'RoDD'))}&times;</b><span>RoDD &middot; best window</span></div>
          </div>
          <p class="desc">{esc(p['sep'][0]) if p['sep'] else ''}</p>
          <div class="fstats">{stats}</div>
          <div class="price-row">
            <div class="price"><span class="now">${p['price']}</span><span class="per">/MO</span></div>
          </div>
          {ADD(p['slug'], p['name'])}
          <div class="cta-row">
            <a class="btn" href="/strategies/{p['slug']}.html">View full data<svg class="ic-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 7h10v10" vector-effect="non-scaling-stroke"/><path d="M7 17 17 7" vector-effect="non-scaling-stroke"/></svg></a>
            <!-- WHOP: replace this product-page link with the Whop checkout link -->
            <a class="btn btn-buy" href="/strategies/{p['slug']}.html" rel="noopener">Get access</a>
          </div>
        </article>"""

# ── screener tables ─────────────────────────────────────────────
def trow(p):
    cells = ""
    for k in ["RoDD", "PF", "Win", "Net", "Max DD", "Trades"]:
        v = bs(p, k)
        cls = []
        if k == "RoDD": cls.append("pf")
        if is_hot(k, v): cls.append("hot")
        c = f' class="{" ".join(cls)}"' if cls else ""
        cells += f'<td{c}>{esc(v)}</td>'
    return f"""<tr>
              <th scope="row"><div class="sys"><div class="sys-name-row"><a class="sys-link" href="/strategies/{p['slug']}.html"><span class="sys-name">{esc(p['name'])}</span></a><span class="sys-real">{esc(p['actual'])}</span>{market_chips(p['meta'])}<span class="chip chip-verified">VERIFIED</span></div><span class="sys-desc">{esc(p['sep'][0][:110]) if p['sep'] else ''}</span></div></th>
              {cells}
              <td class="price-cell">${p['price']}<span class="per">/mo</span></td>
              {ADDCELL(p['slug'], p['name'])}
              <td class="cta-cell"><!-- WHOP: replace this product-page link with the Whop checkout link --><a class="btn btn-buy btn-row" href="/strategies/{p['slug']}.html" rel="noopener">Get access</a></td>
            </tr>"""

def table(tier, label, items):
    rows = "\n            ".join(trow(p) for p in items)
    return f"""<div class="tier-head">
        <span class="tier-tag">{tier}</span>
        <h3>{label}</h3>
        <span class="note">${min(p['price'] for p in items)}&ndash;${max(p['price'] for p in items)}/mo &middot; {len(items)} systems</span>
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
              <th scope="col"><span class="sr-only">Add to selection</span></th>
              <th scope="col"><span class="sr-only">Purchase</span></th>
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
        <span class="note">every figure from the validation playbook &middot; best window</span>
      </div>

      <div class="collections">
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
          <p class="cart-hint">Three or more? <a href="/strategies/pick-3.html">Pick-3 is $499/mo</a>. Want the catalog? <a href="/strategies/all-access.html">All-Access is $999/mo</a> &mdash; combined list ${BN["all_access"]["combined"]:,}.</p>
          <a class="btn btn-buy cart-go" href="#packages">Compare bundles</a>
          <span class="cart-note">Selections are local to this page &mdash; nothing is stored or sent.</span>
        </div>
      </aside>"""

# ── assemble #strategies ────────────────────────────────────────
strategies = f"""<section id="strategies">
    <div class="wrap">
      <div class="sec-head">
        <span class="idx">02 /</span>
        <h2>Strategies</h2>
        <span class="note">{len(S)} live-validated systems &middot; best window and full 2024+ window published</span>
      </div>

      {GLOSSARY}

      {collections}

      <div class="tier-head">
        <span class="tier-tag">TIER 1</span>
        <h3>Flagships</h3>
        <span class="note">${TIER1[-1]['price']}&ndash;${TIER1[0]['price']}/mo &middot; {len(TIER1)} systems</span>
      </div>

      <div class="flagships">

        {chr(10).join(fcard(p) for p in TIER1)}

      </div>

      {table("TIER 2", "Core systems", TIER2)}

      {table("TIER 3", "Session specialists", TIER3)}

      {FOOTNOTE}

      {cart}

    </div>
  </section>"""

doc = re.sub(r'<section id="strategies">.*?</section>', strategies, doc, count=1, flags=re.S)

# ── bundles section ─────────────────────────────────────────────
book_lis = "".join(
    f'<li><a class="sys-link" href="/strategies/{b["slug"]}.html">{esc(b["name"])}</a>'
    f'<span class="bk-int">{esc(b["actual"]).upper()} · ${b["price"]:,}/MO SOLO</span></li>'
    for b in B)
inc_check = ('<svg class="ic-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
             'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
             '<path d="M20 6 9 17l-5-5" vector-effect="non-scaling-stroke"/></svg>')
packages = f"""<section id="packages">
    <div class="wrap">
      <div class="sec-head">
        <span class="idx">03 /</span>
        <h2>Bundles</h2>
        <span class="note">cancel anytime through whop &middot; annual = 2 months free</span>
      </div>

      <article class="pack pack-books">
        <div class="books-head">
          <h3><a class="sys-link" href="/strategies/the-books.html">The Books</a></h3>
          <span class="chip chip-mkt">IN-HOUSE ENGINES</span>
        </div>
        <p class="sub">The four engines we run ourselves &mdash; multi-leg routers, live-validated, both windows published. Sold separately from ${min(b['price'] for b in B):,}/mo; all four together under the price of any two.</p>
        <ul class="books-list">{book_lis}</ul>
        <div class="books-foot">
          <div class="amount"><s class="was">${BN['books_all']['combined']:,}<span class="sr-only"> combined solo price,</span></s>${BN['books_all']['price']:,}<small>/mo</small></div>
          <div class="books-ctas">
            <a class="btn" href="/strategies/the-books.html">View details<svg class="ic-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 7h10v10" vector-effect="non-scaling-stroke"/><path d="M7 17 17 7" vector-effect="non-scaling-stroke"/></svg></a>
            <!-- WHOP: replace this product-page link with the Whop checkout link -->
            <a class="btn btn-buy" href="/strategies/the-books.html" rel="noopener">Get the books</a>
          </div>
        </div>
      </article>

      <div class="packs-2">

        <div class="pack popular">
          <span class="flag">BEST VALUE</span>
          <h3><a class="sys-link" href="/strategies/all-access.html">All-Access</a></h3>
          <div class="amount"><s class="was">${BN['all_access']['combined']:,}<span class="sr-only"> combined list price,</span></s>$999<small>/mo</small></div>
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

        <div class="pack">
          <h3><a class="sys-link" href="/strategies/pick-3.html">Pick-3</a></h3>
          <div class="amount"><s class="was">${BN['pick3']['top3']:,}<span class="sr-only"> worth up to,</span></s>$499<small>/mo</small></div>
          <p class="sub">Any three systems of your choice &mdash; worth up to ${BN['pick3']['top3']:,}/mo solo.</p>
          <ul>
            <li>{inc_check}<span>Any 3 validated systems from any tier</span></li>
            <li>{inc_check}<span>Swap your picks monthly</span></li>
            <li>{inc_check}<span>TradingView invite-only scripts, activated within 24h</span></li>
          </ul>
          <!-- WHOP: replace this product-page link with the Whop checkout link -->
          <a class="btn btn-buy" href="/strategies/pick-3.html" rel="noopener">Get pick-3</a>
        </div>

      </div>

      <p class="banner">Annual on anything = <b>2 months free</b></p>
    </div>
  </section>"""

doc = re.sub(r'<section id="packages">.*?</section>', packages, doc, count=1, flags=re.S)

# ── ticker, stats strip, hero lede, finder prices, counts ───────
tick_names = [(p["name"].upper()) for p in sorted(S, key=lambda x: -num(bs(x, "RoDD")))[:7]]
tick = "".join(f"<span>{esc(n)} · VERIFIED</span>" for n in tick_names)
half = (f"<span>{len(S)} SYSTEMS · 4 BOOKS</span>"
        f"<span>SESSION: SYDNEY → SHANGHAI → FRANKFURT → NEW YORK</span>"
        + tick +
        f"<span>MARKETS: MNQ · NQ · MGC · SI · ES</span>"
        f"<span>DELIVERY: TRADINGVIEW INVITE-ONLY · ACTIVATED WITHIN 24H</span>")
doc = re.sub(r'(<div class="ticker-track">\s*).*?(\s*</div>\s*</div>\s*</div>)',
             lambda m: m.group(1) + half + half + m.group(2), doc, count=1, flags=re.S)

stats_strip = f"""<ul class="stats wrap">
    <li><b>{len(S) + len(B)}</b><span>Validated products</span></li>
    <li><b>5</b><span class="oneline">MNQ·NQ·MGC·SI·ES</span></li>
    <li><b>2&times;</b><span>Windows published</span></li>
    <li><b>24h</b><span>Activation window</span></li>
  </ul>"""
doc = re.sub(r'<ul class="stats wrap">.*?</ul>', stats_strip, doc, count=1, flags=re.S)

doc = re.sub(r'<p class="lede">.*?</p>',
    f"""<p class="lede">
          Goal33 sells the session systems we actually run: {len(S)} live-validated strategies and four
          in-house books across MNQ, NQ, MGC, SI, and ES futures. Every figure comes from the validation
          playbook &mdash; best window and full 2024+ window, both published. TradingView invite-only
          scripts, activated within 24h. Checkout runs through Whop.
        </p>""", doc, count=1, flags=re.S)

for old, new in [("$4,999", "$2,999"), ("all four in-house engines · each also solo at $1,499/mo", f"all four in-house engines · solo from ${min(b['price'] for b in B)}/mo"),
                 ("each also solo at $1,499/mo", f"solo from ${min(b['price'] for b in B)}/mo"),
                 ("Start with one system from $59/mo", f"Start with one system from ${min(p['price'] for p in S)}/mo"),
                 ("from $59/mo", f"from ${min(p['price'] for p in S)}/mo")]:
    doc = doc.replace(old, new)

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
block = ("/* CARTGEN:rules " + chr(8212) + " generated from catalog2.json; do not hand-edit */" + NL
         + incs + NL
         + reveals + " {" + NL
         + "  display: flex; align-items: center; justify-content: space-between; gap: var(--sp-3);" + NL
         + "  padding: var(--sp-2) var(--sp-4); border-bottom: 1px solid var(--line);" + NL + "}" + NL)
css = re.sub(r"/\* CARTGEN:rules.*$", lambda m: block, css, flags=re.S)
open(css_path, "w", encoding="utf-8").write(css)
print("CARTGEN css region regenerated:", len(S), "increment rules")
