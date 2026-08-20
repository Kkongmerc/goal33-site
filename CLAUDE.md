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

Product pages are **generated, never hand-edited**. The chain:

```
_tools/catalog.md            <- SOURCE OF TRUTH (owner-supplied stats + rulings)
  -> python _tools/parse_catalog.py   -> _tools/catalog.json
  -> python _tools/gen_pages.py       -> strategies/*.html (39), 404.html,
                                         success.html, sitemap.xml
```

Also in `_tools/`: `names.json` (slug -> display name; old names are subtitles),
`estimates.json` (fill-ins for missing stats), `charts.py` (equity-path generator).

**Workflow for any data/product change:**
1. Edit `_tools/catalog.md` (record owner rulings inline, dated).
2. Run parse, then gen (commands above; plain Python 3, no deps).
3. If `assets/main.css` changed at all: recompute its md5 and restamp every page —
   `gen_pages.py` stamps its own output automatically; `index.html` must be updated
   to the same `?v=` by hand/sed. All 42 pages must share one version string.
4. Verify, commit, push.

`index.html` is the one hand-maintained page. Keep its stats identical to the sheet.

## Hard content rules (violations have been caught and reverted before)

1. **Every number must trace to `_tools/catalog.md` or `estimates.json`.** No
   invented stats, ever. Estimated values carry an `EST` tag (`.est-tag`) and never
   glow; derived values (e.g. RoDD = Net ÷ MaxDD from verified figures) display as
   verified. Internal consistency must hold: Net = MaxDD × RoDD on every row.
2. **Never take performance numbers from Pine script headers** (stale pre-audit
   figures). Only current TradingView runs, window stated. The owners' vetted
   playbook export is the source for stat updates.
3. **Sydney Session Rider ("First Light") never displays a win rate.** Sheet order.
4. **The four Book compositions stay placeholder** (EXCLUSIVE slots) until Collin
   explicitly approves publishing them. The Books themselves are sellable products.
5. **Required disclaimer verbatim** on every page (footer + strategies section on
   index). Never reword it.
6. **Never put the owners' Pine repo filenames anywhere in this repo or site.**
7. Every buy CTA keeps its adjacent `<!-- WHOP: ... -->` comment. Buy links point
   at product pages until real Whop checkout links replace them (grep `WHOP:`).
8. Months-green claims: only Cascade ("14 of 15 months green") until per-system
   data arrives.

## Brand system (verifiers enforce this)

- Mint `--accent #56C8A2` = data, wins, VERIFIED status. Teal-black surfaces.
- Amber `--buy #ED9B40` = **only** purchase CTAs, deal badges, and standout stats
  (`.hot` — thresholds: PF≥2, Win≥80%, RoDD≥4, n≥600, Net≥$150k; EST never glows).
- Red = retired (drawdowns display plain). No other colors.
- Type: Chakra Petch (display) / JetBrains Mono (all numerals, tabular-nums) /
  Inter (prose). `--fs-*` and `--sp-*` tokens only; nothing under 11px.
- Every fg/bg pair ≥ 4.5:1 — the table in `main.css`'s header is the ledger.
- Value doctrine: **PF is the front-of-store selling stat; RoDD (backed by n) is
  the cross-catalog value metric.**
- Strategy display names are the "cool names" (The Verdict, The Market Maker, …)
  from `_tools/names.json`; original names appear as subtitles. Slugs/URLs never
  change on rename.

## Pricing (current)

Tier 1 $199–249 · Tier 2 $99–129 · Tier 3 $59–79 · NY Open Pro special $239
(anchor $299, 20% off) · Pick-3 $499 · All-Access $999 (combined value $3,528
shown struck; **excludes the Books**) · Books $1,499 each / $4,999 all four ·
Annual = 2 months free. Deals always show the combined price struck out.

## What's pending (don't "fix" these — they're waiting on data)

- `$10K SIMULATION` panels show TBD and calendars are empty grids **on purpose** —
  they fill when the owners' standardized $10k TradingView runs arrive (populate
  `SIM_DATA` in `gen_pages.py` / extend the pipeline).
- Equity charts are labeled *illustrative, fitted to published stats* — replaced by
  real curves when trade-level data lands.
- Terms/Privacy pages: TODO comment in the index footer.

## Verification habits that caught real bugs here

Before pushing: grep for secrets (`sk_`, `sessionid`, `api_key`) in committed
files; zero `<script>`/`style=`; tag/brace balance; every `/strategies/*.html`
href resolves; stats spot-check against the sheet; no `09:30` claims on The Market
Maker (it anchors the **10:00 ET key open**). Serve locally with
`python -m http.server` and eyeball mobile (~375px) — the tables scroll inside
their containers; the page itself must never scroll horizontally.

Never commit: `.claude/`, `.mcp.json`, credentials of any kind (`.gitignore`
already guards the first two). This repo is public and Pages serves everything in
it — assume anything committed is world-readable.
