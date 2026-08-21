# goal33systems.com — how everything runs

Static storefront for Goal33 Systems (futures trading strategies sold via Whop +
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

**Pricing formula** (strategies): `eff = RoDD x min(1, sqrt(n/300))`;
`price = round10($159 + 12 x eff^1.15 - $60) - 1`. The four Books are priced
by hand ABOVE the formula ($589-$1,189 solo; all four $2,999) — books must
stand out price-wise. All-Access $999 excludes the Books; Pick-3 $499.

**Catalog policy**: only LIVE entries from the playbook are listed. Excluded
permanently until re-adjudicated: the nine NT8 port standalones, the base
LVL-5M (TV run still queued), goal2 RTY (PF 1.06), and anything the playbook
marks unconfirmed. Per-strategy Pine SETTINGS (stops, targets, offsets, slots)
are never published. The Market Maker is ONE product carrying both NYO engines.

**Workflow for any data/product change:**
1. Owner supplies a new playbook export; re-curate catalog2.json off-repo.
2. Run gen_pages, then rebuild_index, then gen_plan (order matters:
   rebuild_index regenerates the cart rules in main.css, so the css hash
   moves after it runs).
3. Recompute the css hash and restamp ALL pages (index, plan, success, 404,
   strategies/*) to the same `?v=` — a one-liner over every html file.
4. Verify, commit, push.

**Plan-finder honesty rule** (enforced in gen_plan.py): if the computed best
trio for a Pick-3 seeker is worth less than the $499 bundle price, the page
recommends the cheaper path instead (The Starter if it IS that trio, otherwise
"buy the three solo") — never delete this branch to make Pick-3 sell better.

## Hard content rules (violations have been caught and reverted before)

1. **Every number must trace to `_tools/catalog2.json`.** No invented stats and
   no estimates — the EST system is retired. Both validation windows (best +
   full 2024+) are published for every product.
2. **Never take performance numbers from Pine script headers** (stale pre-audit
   figures). Only current TradingView runs, window stated. The owners' vetted
   playbook export is the source for stat updates.
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
7. Every buy CTA keeps its adjacent `<!-- WHOP: ... -->` comment. Buy links point
   at product pages until real Whop checkout links replace them (grep `WHOP:`).
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
- Strategy display names are the "cool names" (Spartacus, The Market Maker, …)
  embedded in catalog2.json; original names appear as subtitles. Slugs/URLs never
  change on rename.

## Pricing (current — formula-driven, see pipeline section)

Strategies $119–$509 by the RoDD-x-sample formula · Books $589/$889/$989/$1,189
solo, $2,999 all four · All-Access $999 (combined $4,339 struck; excludes
Books) · Pick-3 $499 (worth up to $1,327 struck) · Annual = 2 months free.
Deals always show the combined price struck out.

## What's pending (don't "fix" these — they're waiting on data)

- Daily-results calendars are empty grids **on purpose** — they fill when the
  owners export daily P&L per system.
- Equity charts are labeled *illustrative, fitted to published stats* — replaced by
  real curves when trade-level data lands.
- Terms/Privacy pages: TODO comment in the index footer.

## Verification habits that caught real bugs here

Before pushing: grep for secrets (`sk_`, `sessionid`, `api_key`) in committed
files; zero `<script>`/`style=`; tag/brace balance; every `/strategies/*.html`
href resolves; stats spot-check against the sheet; the Market Maker page describes both NYO engines honestly. Serve locally with
`python -m http.server` and eyeball mobile (~375px) — the tables scroll inside
their containers; the page itself must never scroll horizontally.

Never commit: `.claude/`, `.mcp.json`, credentials of any kind (`.gitignore`
already guards the first two). This repo is public and Pages serves everything in
it — assume anything committed is world-readable.
