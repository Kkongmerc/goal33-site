"""Generate plan.html — the standalone Find-your-plan questionnaire.

Pure-CSS logic: radios + :has() reveal one pre-rendered recommendation per
answer combo. Every recommendation is COMPUTED here from catalog2.json by
fixed rules (no hand-picked favourites, no invented numbers):

  budget cap (max drawdown the buyer can hold)  ->  eligible = best-window Max DD <= cap
  temperament t1 steady  -> highest Win%   among eligible
  temperament t2 balanced-> highest RoDD   among eligible
  temperament t3 swings  -> highest Net    among eligible

Trios are the top three of the same sort, bought solo. Nav/footer mirror
gen_pages.py — keep them in sync when either changes.
"""
import json, os, sys, html, hashlib
from glyphs import glyph, emblem

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(_HERE)
CAT = json.load(open(os.path.join(_HERE, "catalog2.json"), encoding="utf-8"))
S, B, BN = CAT["strategies"], CAT["books"], CAT["bundles"]
WHOP_STORE = CAT.get("whop_store") or "/#packages"
def buy_href(p):
    return p.get("whop") or f"/strategies/{p['slug']}.html"
_pr = sorted((s["price"] for s in S), reverse=True)
COMBINED_ALL = sum(_pr)
_mk = []
for _p in S:
    _i = _p["meta"].split("\u00b7")[0].strip().split()[0].strip()
    if _i and _i not in _mk: _mk.append(_i)
MARKETS_PROSE = (", ".join(_mk[:-1]) + " and " + _mk[-1]) if len(_mk) > 1 else (_mk[0] if _mk else "")
# PRE-LAUNCH: an empty catalog cannot honestly recommend anything
PRELAUNCH = not S
SITE = "https://futurestradingbots.com"
CSSV = hashlib.md5(open(os.path.join(BASE, "assets", "main.css"), "rb").read()).hexdigest()[:8]

def esc(s): return html.escape(str(s), quote=False)
def num(v):
    s = str(v).replace("$", "").replace(",", "").replace("%", "")
    m = 1000 if s.endswith("k") else 1
    try: return float(s.rstrip("k")) * m
    except ValueError: return 0.0
def bs(p, k): return p["best"]["stats"].get(k, "—")
def fs(p, k): return (p.get("full") or {}).get("stats", {}).get(k, "—")
def worst_dd(p):
    """Size against the deeper of the two published windows - the site tells
    buyers to judge from the full-window numbers, so the finder must too."""
    return max(num(bs(p, "Max DD")), num(fs(p, "Max DD")))

DISCLAIMER = ("Trading futures involves substantial risk of loss and is not suitable for all investors. "
              "Past performance is not indicative of future results. All published statistics are from "
              "backtested validation runs over the stated windows.")

# ── the recommendation matrix ───────────────────────────────────
BUDGETS = [
    ("b1", "$1k–$5k",  "Room for a ~$4.5k drawdown", 4500),
    ("b2", "$5k–$10k", "Room for a ~$9.5k drawdown", 9500),
    ("b3", "$10k–$25k","Room for a ~$22.5k drawdown", 22500),
    ("b4", "$25k+",    "Deep book — any published drawdown", 10**9),
]
TEMPS = [
    ("t1", "Steady grind",  "High win rate. Long green streaks, shallow pain."),
    ("t2", "Best math",     "Maximum return per dollar of drawdown. The RoDD play."),
    ("t3", "Big swings ok", "Chase the biggest published net. Deeper holes en route."),
]

def sort_key(tkey):
    if tkey == "t1": return lambda p: (-num(bs(p, "Win")), -num(bs(p, "RoDD")))
    if tkey == "t2": return lambda p: (-num(bs(p, "RoDD")), -num(bs(p, "Win")))
    return lambda p: (-num(bs(p, "Net")), -num(bs(p, "RoDD")))

def eligible(cap):
    return [p for p in S if worst_dd(p) <= cap]

def why_line(p, tkey):
    if tkey == "t1":
        return f"Highest win rate that fits this budget: {bs(p,'Win')} across {bs(p,'Trades')} trades."
    if tkey == "t2":
        return f"Best return-on-drawdown that fits: {bs(p,'RoDD')}&times; RoDD on {bs(p,'Trades')} trades."
    return f"Biggest published net that fits: {bs(p,'Net')} — budget for the full {bs(p,'Max DD')} drawdown en route."

def stat_strip(p):
    cells = ""
    for k, lab in [("RoDD", "RoDD"), ("Max DD", "Max DD"), ("Win", "Win"), ("Trades", "n")]:
        cells += f'<div class="prs"><b>{esc(bs(p,k))}</b><span>{lab}</span></div>'
    return f'<div class="pr-stats">{cells}</div>'

def single_card(p, tkey, alt):
    alt_line = (f'<p class="pr-alt">Runner-up: <a href="/strategies/{alt["slug"]}.html">{esc(alt["name"])}</a>'
                f' — {bs(alt,"RoDD")}&times; RoDD, {bs(alt,"Win")} win, {bs(alt,"Max DD")} max drawdown.</p>') if alt else ""
    return f"""<div class="pr-card fc-{p['slug']}">
      <div class="pr-head"><span class="pr-gchip">{glyph(p['slug'], 'glyph g-plan')}</span><div class="pr-id">
        <a class="pr-name" href="/strategies/{p['slug']}.html">{esc(p['name'])}</a>
        <span class="pr-real">{esc(p['actual'])}</span></div>
        <div class="pr-price">${p['price']}<small>/MO</small></div>
      </div>
      <p class="pr-why">{why_line(p, tkey)}</p>
      {stat_strip(p)}
      <div class="pr-ctas">
        <a class="btn" href="/strategies/{p['slug']}.html">View full data</a>
        <!-- WHOP: replace with checkout link ({esc(p['name'])}) -->
        <a class="btn btn-buy" href="{buy_href(p)}" rel="noopener">Get access</a>
      </div>
    </div>"""

def trio_rows(trio, slots=3):
    """Renders up to `slots` rows; any slot with no qualifying strategy is
    left visibly blank rather than filled with something that does not fit."""
    rows = ""
    for p in trio:
        rows += (f'<li>{glyph(p["slug"], "glyph g-row")}<a class="pr-name" href="/strategies/{p["slug"]}.html">{esc(p["name"])}</a>'
                 f'<span class="pr-real">{esc(p["actual"])}</span>'
                 f'<span class="pr-mini">{bs(p,"RoDD")}&times; RoDD · {bs(p,"Win")} win · {bs(p,"Max DD")} DD</span>'
                 f'<span class="pr-solo">${p["price"]}</span></li>')
    for _ in range(max(0, slots - len(trio))):
        rows += ('<li class="pr-empty"><span class="pr-name">Slot open</span>'
                 '<span class="pr-real">nothing else clears this drawdown budget yet</span></li>')
    return rows

RULE_LINE = {"t1": "highest win rates", "t2": "highest RoDD", "t3": "largest published nets"}

def trio_block(trio, tkey):
    """Three strategies for this kind of trader, bought solo. Pick-3 is
    retired, so there is no bundle to weigh against - the recommendation is
    simply the three that fit, and what they cost together."""
    worth = sum(p["price"] for p in trio)
    rule = RULE_LINE[tkey]
    n = len(trio)
    return f"""<div class="pr-card">
      <div class="pr-head"><div class="pr-id"><span class="pr-name">Your three</span>
        <span class="pr-real">{'the ' + rule + ' that fit your drawdown budget' if n == 3 else f'only {n} clear your drawdown budget'}</span></div>
        <div class="pr-price">${worth:,}<small>/MO TOTAL</small></div>
      </div>
      <ul class="pr-trio">{trio_rows(trio)}</ul>
      <p class="pr-why">Chosen by the same rule the shelf is ranked by: the {rule} whose deeper published
      drawdown still fits what you said you can hold. Each is its own subscription &mdash; add or drop any
      of them month to month.</p>
      <div class="pr-ctas">
        <a class="btn btn-buy" href="/#strategies">Open the catalog</a>
      </div>
    </div>"""

# build all combo panels
panels = ""
for bkey, blab, bdesc, cap in ([] if PRELAUNCH else BUDGETS):
    pool = eligible(cap)
    for tkey, tlab, tdesc in TEMPS:
        ranked = sorted(pool, key=sort_key(tkey))
        pick, alt = ranked[0], (ranked[1] if len(ranked) > 1 else None)
        panels += f'<div class="pr" id="r-s1-{bkey}-{tkey}">{single_card(pick, tkey, alt)}</div>\n'
        panels += f'<div class="pr" id="r-s2-{bkey}-{tkey}">{trio_block(ranked[:3], tkey)}</div>\n'

# fleet (all-access) panels — budget-aware
starter_slugs = BN["starter"]["slugs"]
starter_names = [p["name"] for p in S if p["slug"] in starter_slugs] or ["TBD"]
STARTER_OK = set(starter_slugs) <= {p["slug"] for p in S}
fleet_small = f"""<div class="pr" id="r-s3-small">
  <div class="pr-card">
    <div class="pr-head"><div class="pr-id"><span class="pr-name">The Starter</span>
      <span class="pr-real">{esc(' + '.join(starter_names))}</span></div>
      <div class="pr-price"><s class="was">${BN['starter']['combined']}</s>${BN['starter']['price']}<small>/MO</small></div>
    </div>
    <p class="pr-why">At this budget, run the three lowest-drawdown systems first — every one holds under a $9k published max drawdown — then step up to the full shelf once you have lived with them.</p>
    <div class="pr-ctas">
      <a class="btn" href="/strategies/the-starter.html">See The Starter</a>
      <!-- WHOP: replace with checkout link (The Starter) -->
      <a class="btn btn-buy" href="/strategies/the-starter.html" rel="noopener">Start for ${BN['starter']['price']}/mo</a>
    </div>
  </div>
</div>"""
if not STARTER_OK:
    # The Starter's members are not in the published catalog, so recommend the
    # real cheapest way in rather than hiding this branch entirely.
    _cheap = min(S, key=lambda x: x["price"]) if S else None
    fleet_small = f"""<div class="pr" id="r-s3-small">
  <div class="pr-card">
    <div class="pr-head"><div class="pr-id"><span class="pr-name">Start with one</span>
      <span class="pr-real">{esc(_cheap["name"]) if _cheap else "TBD"} &mdash; the smallest step onto the shelf</span></div>
      <div class="pr-price">${_cheap["price"] if _cheap else 0}<small>/MO</small></div>
    </div>
    <p class="pr-why">At this budget, run one system properly before you run several. {esc(_cheap["name"]) if _cheap else ""} is the
    lowest-priced published strategy &mdash; live with its drawdown for a month, then add a second when you have lived with its drawdown.</p>
    <div class="pr-ctas">
      <a class="btn" href="/strategies/{_cheap["slug"] if _cheap else ""}.html">See {esc(_cheap["name"]) if _cheap else ""}</a>
      <!-- WHOP: replace with checkout link ({_cheap["name"] if _cheap else "TBD"}) -->
      <a class="btn btn-buy" href="{buy_href(_cheap) if _cheap else "#"}" rel="noopener">Get it for ${_cheap["price"] if _cheap else 0}/mo</a>
    </div>
  </div>
</div>"""
fleet_big = f"""<div class="pr" id="r-s3-big">
  <div class="pr-card">
    <div class="pr-head"><div class="pr-id"><span class="pr-name">All-Access</span>
      <span class="pr-real">every strategy on the shelf — {len(S)} systems, books excluded</span></div>
      <div class="pr-price"><s class="was">${COMBINED_ALL:,}</s>${BN['all_access']['price']}<small>/MO</small></div>
    </div>
    <p class="pr-why">The whole catalog under one subscription: all {len(S)} live-validated systems across {MARKETS_PROSE}, worth ${COMBINED_ALL:,}/mo solo. Diversify across sessions instead of picking one.</p>
    <div class="pr-ctas">
      <a class="btn" href="/strategies/all-access.html">See All-Access</a>
      <!-- WHOP: replace with checkout link (All-Access) -->
      <a class="btn btn-buy" href="/strategies/all-access.html" rel="noopener">Get All-Access — ${BN['all_access']['price']}/mo</a>
    </div>
  </div>
</div>"""

# books panel — mini deck, same skins as the index band
BOOK_SKIN = {"the-midas": "bk-midas", "the-continuum": "bk-continuum",
             "the-daylight": "bk-daylight", "the-ledger": "bk-vault"}
book_cards = "" if PRELAUNCH else "".join(
    f'<li class="bookcard {BOOK_SKIN[b["slug"]]}">{emblem(b["slug"])}'
    f'<a class="sys-link bk-name" href="/strategies/{b["slug"]}.html">{esc(b["name"])}</a>'
    f'<span class="bk-int">{esc(b["actual"]).upper()}</span>'
    f'<span class="bk-price">${b["price"]:,}<small>/MO SOLO</small></span></li>' for b in B)
books_panel = f"""<div class="pr" id="r-s4">
  <div class="pr-card">
    <div class="pr-head"><div class="pr-id"><span class="pr-name">The Books are next</span>
      <span class="pr-real">our four in-house multi-leg engines</span></div>
    </div>
    <p class="pr-why">The engines we run ourselves are still in validation. When they publish, both windows go up with
    them &mdash; same standard as everything else on this page. Until then, All-Access at ${BN['all_access']['price']}/mo
    is the widest coverage we sell.</p>
    <div class="pr-ctas">
      <a class="btn" href="/strategies/all-access.html">See All-Access</a>
    </div>
  </div>
</div>""" if not B else f"""<div class="pr" id="r-s4">
  <div class="pr-card pr-card-books">
    <div class="pr-head"><div class="pr-id"><span class="pr-name">The Books</span>
      <span class="pr-real">the four in-house engines we run ourselves</span></div>
      <div class="pr-price"><s class="was">${BN['books_all']['combined']:,}</s>${BN['books_all']['price']:,}<small>/MO</small></div>
    </div>
    <ul class="bookdeck bookdeck-mini">{book_cards}</ul>
    <p class="pr-why">Multi-leg routers, live-validated, both windows published. Solo from ${min((b['price'] for b in B), default=0):,}/mo; all four together under the price of any two.</p>
    <div class="pr-ctas">
      <a class="btn" href="/strategies/the-books.html">See The Books</a>
      <!-- WHOP: replace with checkout link (The Books) -->
      <a class="btn btn-buy" href="/strategies/the-books.html" rel="noopener">Get the Books — ${BN['books_all']['price']:,}/mo</a>
    </div>
  </div>
</div>"""

# ── question markup ─────────────────────────────────────────────
def chips(name, opts):
    out = ""
    for oid, lab, sub in opts:
        out += (f'<input class="pq-radio" type="radio" name="{name}" id="{oid}">'
                f'<label class="pq-opt" for="{oid}"><b>{esc(lab)}</b>{f"<span>{esc(sub)}</span>" if sub else ""}</label>')
    return f'<div class="pq-opts">{out}</div>'

scope_opts = [
    ("s1", "One system", "Start focused — a single edge, run properly"),
    ("s2", "Three systems", "Three that clear your drawdown budget, each its own subscription"),
    ("s3", "The whole shelf", "All-Access — every strategy at once"),
    ("s4", "The in-house Books", "The four engines we run ourselves"),
]
budget_opts = [(k, l, d) for k, l, d, _ in BUDGETS]
temp_opts = [(k, l, d) for k, l, d in TEMPS]
exec_opts = [
    ("e1", "Manually", "I take the alerts myself"),
    ("e2", "Automated", "Hands-free, alerts execute at my broker"),
]

qs = f"""
      <input type="checkbox" id="ed-scope" class="pq-edit">
      <fieldset class="pq pq-scope">
        <legend><span class="pq-n">STEP 01</span> <span class="pq-q">What are you shopping for?</span></legend>
        {chips('q-scope', scope_opts)}
      <label class="pq-editlab" for="ed-scope"><span class="sr-only">Change this answer</span></label>
        <label class="pq-close" for="ed-scope">done</label>
      </fieldset>

      <input type="checkbox" id="ed-budget" class="pq-edit">
      <fieldset class="pq pq-budget">
        <legend><span class="pq-n">STEP 02</span> <span class="pq-q">What drawdown budget are you sizing?</span></legend>
        <p class="pq-hint">Not your account size — the open drawdown you could genuinely sit through without pulling the plug. The same number the sizing menu on every product page runs on.</p>
        {chips('q-budget', budget_opts)}
      <label class="pq-editlab" for="ed-budget"><span class="sr-only">Change this answer</span></label>
        <label class="pq-close" for="ed-budget">done</label>
      </fieldset>

      <input type="checkbox" id="ed-temp" class="pq-edit">
      <fieldset class="pq pq-temp">
        <legend><span class="pq-n">STEP 03</span> <span class="pq-q">What kind of ride can you stomach?</span></legend>
        {chips('q-temp', temp_opts)}
      <label class="pq-editlab" for="ed-temp"><span class="sr-only">Change this answer</span></label>
        <label class="pq-close" for="ed-temp">done</label>
      </fieldset>

      <input type="checkbox" id="ed-exec" class="pq-edit">
      <fieldset class="pq pq-exec">
        <legend><span class="pq-n">STEP 04</span> <span class="pq-q">How will you run it?</span></legend>
        {chips('q-exec', exec_opts)}
      <label class="pq-editlab" for="ed-exec"><span class="sr-only">Change this answer</span></label>
        <label class="pq-close" for="ed-exec">done</label>
      </fieldset>
"""

pmt_panel = """<aside class="pr pr-exec" id="r-e2">
        <div class="pmt">
          <div class="pmt-title">PARTNERED WITH PICKMYTRADE</div>
          <p class="pmt-copy">Every system here fires standard TradingView alerts. Through our partner
          PickMyTrade, those alerts route straight to your broker &mdash; Tradovate, NinjaTrader, and more &mdash;
          and execute hands-free. Setup takes minutes, no code.</p>
          <ol class="pmt-steps">
            <li>Connect your broker to PickMyTrade</li>
            <li>Paste our alert template into TradingView</li>
            <li>Alerts fire &rarr; orders execute &mdash; you supervise</li>
          </ol>
          <div class="pmt-cta">
            <a class="btn btn-solid" href="https://pickmytrade.trade/?referral=XcWQwlL2tzFDqd1lxaJDtw" target="_blank" rel="noopener sponsored">Set up PickMyTrade</a>
            <span class="pmt-disc">partner link</span>
          </div>
        </div>
      </aside>
      <aside class="pr pr-exec" id="r-e1">
        <div class="pmt pmt-manual">
          <div class="pmt-title">RUNNING IT BY HAND</div>
          <p class="pmt-copy">Every product page lists its session window and bar time &mdash; most systems fire
          inside one narrow slot per day. Treat the alert as your entry checklist, size with the RoDD menu on
          the product page, and take every signal: the published stats assume no cherry-picking.</p>
        </div>
      </aside>"""

if PRELAUNCH:
    qs = """      <div class="prelaunch">
        <span class="pl-tag">FINDER OFFLINE</span>
        <h3>The plan finder returns with the new lineup.</h3>
        <p>This page matches you to a system by drawdown budget and temperament &mdash; it
        needs a published catalog to do that honestly, and the new one is still in
        validation. Nothing here will guess. It switches back on the day the first
        flagship lands.</p>
        <div class="pl-ctas">
          <a class="btn btn-buy" href="/#strategies">See what is coming</a>
          <!-- DISCORD: community invite -->
          <a class="btn" href="https://discord.gg/BBXDDn9pCD" target="_blank" rel="noopener">Get told when it lands</a>
        </div>
      </div>"""
    panels = fleet_small = fleet_big = books_panel = pmt_panel = ""

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; base-uri 'none'; form-action 'none'; upgrade-insecure-requests">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>Find your plan — FuturesTradingBots</title>
<meta name="description" content="Answer four questions — drawdown budget, temperament, scope, execution — and get a specific recommendation: named systems sized to a drawdown you can actually hold.">
<meta name="theme-color" content="#051014">
<meta property="og:title" content="Find your plan — FuturesTradingBots">
<meta property="og:site_name" content="FuturesTradingBots">
<meta property="og:description" content="Four questions to a specific, named recommendation — sized to the drawdown you can actually hold.">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}/plan.html">
<link rel="canonical" href="{SITE}/plan.html">
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
      <a class="nav-plan" href="/plan.html" aria-current="page">Find your plan</a>
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
  <section class="plan-hero">
    <div class="wrap">
      <p class="plan-kicker">PLAN FINDER</p>
      <h1>Find your <span class="mint">plan</span></h1>
      <p class="plan-sub">Four answers. One specific recommendation &mdash; named systems, or a custom
      three named systems &mdash; sized to the drawdown you can actually hold, chosen by the same math
      that ranks the shelf. Runs entirely in your browser: this page ships zero script, so your answers
      never leave it.</p>
    </div>
  </section>

  <div class="wrap">
    <div id="plan">
      <div class="plan-prog" aria-hidden="true"><span class="pp pp-1"></span><span class="pp pp-2"></span><span class="pp pp-3"></span><span class="pp pp-4"></span></div>
      <div class="plan-qs">
      {qs}
      </div>
      <section class="plan-results" aria-live="polite">
        {panels}
        {fleet_small}
        {fleet_big}
        {books_panel}
        {pmt_panel}
      </section>
      <p class="plan-update">change any answer &mdash; the recommendation updates instantly</p>
    </div>
  </div>
</main>

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
    <div class="copyright">&copy; 2026 FuturesTradingBots &middot; futurestradingbots.com</div>
  </div>
</footer>

</body>
</html>
"""

open(os.path.join(BASE, "plan.html"), "w", encoding="utf-8").write(page)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
n_panels = page.count('class="pr"')
print(f"plan.html written: {n_panels} result panels, css v{CSSV}")
