# futurestradingbots.com — how everything runs

Static storefront for FuturesTradingBots (futures trading strategies sold via Whop +
TradingView invite-only scripts). This file is the operating manual. Read it fully
before changing anything — most of the rules below exist because a verifier or the
owners caught a real problem.

## Architecture (deliberate — do not "improve" it away)

- **Hosting**: GitHub Pages from `main`. `git push` = deploy, live in ~1–2 min
  (Cloudflare fronts the domain; give it one extra minute of cache).
- **Zero JavaScript. No exceptions.** No `<script>` tags anywhere. The FAQ is
  `<details>`, the ticker/dial animations are CSS, the plan-finder quiz is CSS
  `:has()` logic. This is the site's security story ("a storefront can't leak what
  it never holds") and it is marketed as such on the page.
- **Strict CSP** via `<meta http-equiv="Content-Security-Policy">` on every page:
  `default-src 'none'`, styles/fonts only from self + Google Fonts. Consequences:
  **no inline `style=""` attributes ever** (style-src has no unsafe-inline), no new
  external origins, SVG styling via classes or presentation attributes only.
- **One stylesheet**: `assets/main.css`, loaded with a content-hash cache-buster
  (`?v=xxxxxxxx`). The header comment in that file carries the WCAG contrast table —
  update it when you touch colors.

## The data pipeline (the most important thing here)

Product pages AND the index catalog sections are **generated, never hand-edited**:

```
_tools/catalog2.json          <- SOURCE OF TRUTH (curated from the owners'
                                 validation playbook; live-validated only)
  -> python _tools/gen_pages.py      -> strategies/*.html, success.html,
                                        404.html, sitemap.xml (deletes stale pages)
  -> python _tools/rebuild_index.py  -> index.html catalog sections (ticker,
                                        stats strip, lede, #strategies, #packages)
                                        + the CARTGEN css region in main.css
  -> python _tools/gen_plan.py       -> plan.html (the Find-your-plan page:
                                        every recommendation COMPUTED from
                                        catalog2 by fixed rules — win/RoDD/net
                                        sort within a drawdown-budget cap)
```

`_tools/glyphs.py` is the shared per-product SVG mark library (one glyph per
strategy slug + the four book emblems) imported by rebuild_index and gen_plan —
add a mark there when a new product lands, or its glyph slot renders empty.

`catalog2.json` is curated OFF-REPO from the owners' playbook export (the raw
playbook contains Pine filenames and research paths — never commit it). Each
product carries: cool name + actual name, meta, BEST WINDOW + FULL 2024+ WINDOW
stat sets, price, legs, what-separates lines, and warnings.

**Promo code (the one field to change for a new marketer):** `catalog2.json` top-level
`promo` = `{"code": "AFT", "line": "Use code {code} at checkout", "note": "..."}`. The
generators substitute `{code}` into `line` and render it next to every buy button and in
the buy box — edit `promo.code`/`promo.line` and regenerate to change it site-wide. Zero
JS means one code per build: a marketer's own tracked code is their Whop referral link
(applies automatically at checkout); `promo` is only the default code shown to buyers who
arrive without one.

**Monthly special (the second field to change each month):** `catalog2.json` top-level `special` =
`{"active": true, "label": "September special", "line": "First month {pct}% off with code {code}",
"pct": 30, "code": "SEPT30", "ends": "30 Sep 2026"}`. gen_pages renders it as the coloured strip
above the buy button on every product/bundle page and rebuild_index as one line above the index
tables; `{pct}` and `{code}` are substituted into `line`, `ends` prints after it. Set `active` to
false and nothing renders anywhere. All copy comes from this object - never hand-write a special
into a template. No scarcity counters, no fake deadlines: `ends` is the real end date.

**Pricing formula** (strategies): `eff = RoDD x min(1, sqrt(n/300))`;
`price = round10($159 + 12 x eff^1.15 - $60) - 1`. The four Books are priced
by hand ABOVE the formula ($589-$1,189 solo; all four $2,999) — books must
stand out price-wise. All-Access $999 excludes the Books. Pick-3 is retired.

**Catalog policy**: only LIVE entries from the playbook are listed. Excluded
permanently until re-adjudicated: the nine NT8 port standalones, the base
LVL-5M (TV run still queued), goal2 RTY (PF 1.06), and anything the playbook
marks unconfirmed. Per-strategy Pine SETTINGS (stops, targets, offsets, slots)
are never published.

**Workflow for any data/product change:**
1. Owner supplies a new playbook export; re-curate catalog2.json off-repo.
2. Run gen_pages, then rebuild_index, then gen_plan (order matters:
   rebuild_index regenerates the cart rules in main.css, so the css hash
   moves after it runs).
3. Recompute the css hash and restamp ALL pages (index, plan, success, 404,
   strategies/*) to the same `?v=` — a one-liner over every html file.
4. Verify, commit, push.

**Plan-finder honesty rule** (enforced in gen_plan.py): if the computed best
trio recommendation must stay three SOLO subscriptions. Pick-3 is retired, so
there is no bundle to weigh a trio against; `trio_rows` renders any slot with
no qualifying strategy as a visibly blank dashed row rather than padding it
with something that does not clear the buyer's drawdown budget.

## CURRENT STATE (5 live products, Whop + Discord wired)

Five RoDD-board rows are PUBLISHED in `catalog2.json` -> `strategies[]`:
continuum ($909) / midas ($759) / aftershock ($699) / slipstream ($649) /
ignition ($299) — board rows 1, 2, 3, 5 and 6. **Row 4 (MNQ Strong Book) was
pulled by the owners**; its glyph, `fc-strongbox` skin and archive entry are
intact, so republishing is one tuple away. Prices are formula-driven from
replayed best-window RoDD x n — ignition is cheap because n=66, which is the
formula working, not a discount.

Every number is a closed-trade replay of the committed TradingView export the
owners' validation board used (verified digit-for-digit against the board).
**Real trade data lives in `_tools/trades/<slug>.json`** (equity points, daily
P&L, closed-trade list): it powers the real equity curves, the filled daily
calendars, and the product pages' Trade log tab.

**Whop is LIVE.** `whop_store` in catalog2.json plus a `whop` field per
strategy, consumed by `buy_href()` in all three generators — swapping a
product-page link for a direct checkout link is a one-field edit, never a code
change. `ingest_top5.py` carries them through a re-ingest. Bundle CTAs have no
Whop product yet and point at the storefront. Discord is wired everywhere
(`discord.gg/BBXDDn9pCD`); support routes there, and there is no support email
anywhere on the site.

**THE BASELINE (read before touching any headline figure).** Raw net is NOT
comparable across products: it mixes drawdown depth AND position size. That is
why Continuum ($72.5k) once looked worse than Midas ($119.5k) despite ranking
above it on every risk-adjusted measure. Every headline slot — carousel pane,
card top-right hero, product-page hero — leads with net normalised to a fixed
`baseline_dd` ($5,000): `RoDD x 5000`. It is scale-invariant, it puts the five
in board order, and it states RoDD in language a buyer parses. The RoDD
multiple stays as a supporting figure; actual net stays in the stat tiles.
**If you add a headline figure anywhere, use the baseline, not net.**

Bundle pages generate on their own guards, NOT one flag: `HAS_BUNDLES`
(strategies exist) writes all-access; `HAS_BOOKS_BUNDLE` writes the-books;
`HAS_STARTER` writes the-starter only while every member slug is still in the
catalog. **Pick-3 is retired** — removed as a product, its page no longer
generated, and the plan finder recommends three solo subscriptions instead of
a bundle. Struck "combined" prices are summed from the live catalog at build
time, never stored constants. Books stay pending (`books[]` empty -> #packages
renders a 'Books are next' band and the plan finder's books panel becomes a
pending band). The ticker's market list and product counts are catalog-derived
too. The hero carousel runs 5 slots. Cool names are lineage picks and
renameable — **slugs are frozen once a Whop product exists for them.**

## PRE-LAUNCH MODE (dormant, not active)

Every generator still detects an empty catalog (`PRELAUNCH`) and renders "new
lineup loading" placeholder bands instead of products — no product/bundle pages
written, plan finder offline notice, carousel showing five reserved slots.
**This path is dormant while five products are live.** It is kept working on
purpose: `.cf-pane:not(:has(.cf-spark))` still centres chartless panes, and the
previous catalog plus rendered examples live in `_tools/archive/`.

**To publish a product:** fill one slot from `catalog2.json` -> `drafts`
(`_template_strategy` documents every field), move it into `strategies[]` (or
`books[]`), add its glyph in `_tools/glyphs.py` and an `fc-<slug>` colour skin
in main.css, drop its replayed trade data at `_tools/trades/<slug>.json`, then
run the three generators and restamp. Append the product to
`D:/Downloads/publish-queue.md` at the same time — that ledger is what the Whop
operator works from.

## Hard content rules (violations have been caught and reverted before)

1. **Every number must trace to `_tools/catalog2.json`.** No invented stats and
   no estimates — the EST system is retired. Both validation windows (best +
   full 2024+) are published for every product.
2. **Never take performance numbers from Pine script headers** (stale pre-audit
   figures). Only current TradingView runs, window stated. The owners' vetted
   playbook export is the source for stat updates.
3b. **Product-page chart is real, and hoverable without JS**: `real_chart()`
   bakes ~110 invisible hover strips (`.hp` > `.hp-hit`) into the SVG, each
   revealing its own crosshair line, dot and value tag on `:hover` — the
   zero-JS equivalent of a charting library's crosshair. Calendar day values
   are compacted (k-format, minus sign kept so colour is never the only
   signal) with the exact figure in a native `title`; the calendar renders in
   a full-width `.pdp-wide` band BELOW `.pdp-cols`, because inside the 611px
   main column its day cells crowd their borders. The Trade log publishes a
   duration BUCKET ("< 10m", "1-2h"), never clock times.

3. **The RoDD sizing menu is the centerpiece of every product page** — radios
   styled as a slider; undersized budgets tint the menu amber/red. Red threshold
   for The Collector includes its $12.3k worst session (sizing guard).
4. **Book leg NAMES are shown; composition dials stay proprietary.** Never
   publish per-strategy Pine settings (stops, TPs, offsets, entry slots).
5. **Required disclaimer verbatim** on every page (footer + strategies section on
   index). Never reword it.
6. **Never put the owners' Pine repo filenames anywhere in this repo or site.**
   The same goes for the owners' personal names — published copy says
   "our team", never an individual (a first-name "ruling" label leaked
   once through the catalog window labels; curate.py now scrubs names).
7. Every buy CTA keeps its adjacent `<!-- WHOP: ... -->` comment. **Whop is
   LIVE**: the store is `whop_store` in catalog2.json and each strategy carries
   a `whop` field, both consumed by `buy_href()` in all three generators — so
   swapping a product-page link for a direct checkout link is a one-field edit,
   never a code change. Bundle CTAs (All-Access, Starter, Books) have no
   Whop product yet and still point at their own pages (grep `WHOP:`).
8. Warnings that survived owner review (Pendulum tariff week, Collector sizing
   guard) are published as trust devices — do not remove them.

## Brand system (verifiers enforce this)

- Mint `--accent #56C8A2` = data, wins, VERIFIED status. Teal-black surfaces.
- Amber `--buy #ED9B40` = **only** purchase CTAs, deal badges, and standout stats
  (`.hot` — thresholds: PF≥2, Win≥80%, RoDD≥4, n≥600, Net≥$150k; formula-driven).
- Red = retired (drawdowns display plain). Violet #9D5CFF = category leaders only.
- **Identity colors** (owner-approved exception): each Book and each flagship
  card carries its own color on name/emblem/chrome ONLY (`.bk-*` / `.fc-<slug>`
  skins in main.css) — data figures stay mint/amber/violet. Every identity
  color is in the header ledger; keep any new one ≥ 4.5:1 on panel. The ten
  special products (6 flagships + 4 books) also get identity-THEMED product
  pages: gen_pages puts `pdp-theme fc-<slug>` on <body>, which remaps the
  --buy channel page-wide.
- **DD medals**: Max DD ≤ $2k renders gold, ≤ $5k neon green (`dd_cls` in the
  generators — change thresholds there, never hand-color a cell). Flagship
  cards star their rank-picked standout stat; rank tags show "#N" only for
  top-3 (honesty rule — never fake a rank).
- **Performance doctrine** (the page lagged twice): every INFINITE animation
  on this site keyframes ONLY `opacity` or `transform` — compositor-only, no
  per-frame paint. Glows are painted statically and pulsed via opacity (the
  carousel dots light through an `::after` layer, the nav ember lives on a
  pseudo, the violet `.lead` aurora breathes opacity over a static shadow).
  Never keyframe box-shadow / text-shadow / filter / background-color on an
  infinite loop; finite ≤2-cycle pulses are the only exception. No
  `-webkit-box-reflect`. Below-fold sections use `content-visibility: auto`
  with measured `contain-intrinsic-size` values (#packages stays exempt — cv's
  paint containment clips the fixed starter popup inside it). The hero
  carousel depth-sorts via preserve-3d — do NOT add z-index to its poses or
  keyframes (stepped z caused visible pane-order jumps).
- **Carousel contract** (v7): two modes on radio `#cf-0` (auto, default) vs
  `#cf-1..6` (hold). Radios MUST stay `position: fixed` — anything else makes
  label clicks scroll the page. Selection changes use per-slot
  transition-delays (the cascade that reads as cycling); the play pill
  re-checks `#cf-0`. The cover-flow CSS block between its banner comment and
  the 760px media rule is EXCISED WHOLESALE by carousel regens — never insert
  unrelated rules inside that span (the SITE SYSTEMS region right after it
  exists because cv/snap/creed once got eaten this way).
- Type: Chakra Petch (display) / JetBrains Mono (all numerals, tabular-nums) /
  Inter (prose). `--fs-*` and `--sp-*` tokens only; nothing under 11px.
- Every fg/bg pair ≥ 4.5:1 — the table in `main.css`'s header is the ledger.
- Value doctrine: **RoDD backed by n is THE metric** — hero stat on every card
  and product page, the pricing input, and the sizing menu. PF supports.
- Strategy display names are the "cool names" (Continuum, Midas, Ignition, …)
  embedded in catalog2.json; original names appear as subtitles. Slugs/URLs never
  change on rename.

## Pricing (banded by average monthly profit; stored in the catalog)

The RoDD-x-sample formula is RETIRED. Prices are set from average monthly
profit at the shown multiplier and STORED in `catalog2.json` -> each
strategy's `price`; the generators read them and never recompute:
<=$10k -> $75 · $10-14k -> $125 · $14-18k -> $200 · $18-20k -> $275 ·
$20k+ -> $350. Books and combos are priced by hand ABOVE the band:
Midas $550 · Triad $700 · Slipstream $700 · Continuum $950 · The Books
$1,200 · All-Access $1,500 (books INCLUDED; $1,200/mo with 3 months up
front). Annual = 10x monthly ("2 months free"). **Pick-3 is retired.**
Deals always show the combined price struck out, computed from the catalog
at build time. When a band changes, edit the `price` fields and regenerate
— never hand-edit a price into a page.

Founding affiliate commission **15%** recurring; buyer referral discount 10%.
Terms promise the rate you earn it at is the rate you keep — if the rate ever
changes, use per-affiliate rates or a dated roster rather than editing the
global rate.

## What's pending

- **Books/bundles**: `books[]` empty. The bands and guards are all in place.
- **Direct Whop checkout links**: product-page links are wired in the
  meantime; swapping them is one `whop` field per product.
- **Whop store slug** still reads `goal33systems`, the old brand — a buyer
  clicking "Get access" lands on a differently-named store at the moment they
  decide to pay.
- **Per-strategy contract counts** (see the honesty section below).
- Terms section 09: `LEGAL:` marks the state-of-organization blank.

## KNOWN DATA ISSUE — position size (do not paper over this)

The site used to assert "one-contract scale" in seven places, including the
refund guarantee's measurement basis in Terms section 03. **It was false**, and
the proof needs no statistics: Ignition's 132 modal winners each moved exactly
+0.50 NQ points, which is $10.00 gross at ONE contract, yet each netted $40.00.
Net cannot exceed gross. Slipstream is the same shape. A P&L-lattice check
agrees — continuum and aftershock sit on a 1-lot lattice, slipstream on 2,
ignition on 5; midas is a multi-leg book and does not resolve to one number.

The copy now says only what is verifiable: figures are "at the position size
each strategy's validated run used". **Do not restore a specific scale claim
without confirming `qty` in the Pine configs.** Once confirmed, publishing the
count per product is strictly better than the current wording. Nothing about
rankings or prices changes either way: RoDD, PF and win rate are
scale-invariant.

## Verification habits that caught real bugs here

Before pushing, run over every shipped page: zero `<script>` and zero
`style=`; CSP meta present; brace/tag balance; every internal href resolves;
no `mailto:`; no dead `btn-buy href="#"`; no research identifiers (`.pine`,
cell IDs like `PBV-S07`/`Q429`/`goal13`, personal names); no stale figures
(a retired rate, a removed product). Then serve locally and check **1400px and
375px**: the page must never scroll horizontally, tables scroll inside their
own containers, and nothing collides.

**Verify in the browser, not just the file.** Bugs found only by rendering:
the flagship name overlapping the headline figure at 375px; a stretched
fifth card; the sizing menu recommending a budget the full record would have
wiped; the carousel's bright pane flying across mid-switch.

**grep -c exits 1 when it counts zero.** A watcher checking "the bad string is
gone" reports failure on success. Read the output, not the exit code.

**The cache-buster is not the served hash.** Pages request
`main.css?v=<hash>`; fetching bare `main.css` can return a stale cached copy.
Always verify against the versioned URL.

**Write patch scripts to the scratchpad and run them** — heredocs mangle
backslashes and quotes inside Python strings, and Python 3.10 rejects
backslashes inside f-string expressions.

**Assert before you replace.** Every patch script asserts its anchor exists.
Two real half-removals happened when a regex matched an opening tag but left
the body behind.

Never commit: `.claude/`, `.mcp.json`, credentials of any kind. This repo is
public and Pages serves **everything** in it — `_tools/` included, because
`.nojekyll` disables Jekyll's `_`-prefix skip. `robots.txt` disallows
`/_tools/`, `/CLAUDE.md` and `/README.md`, but that is a crawler request, not
access control. Assume anything committed is world-readable.
