"""Parse catalog.md (source of truth) into structured JSON for product-page generation."""
import json, os, re, sys, unicodedata
_HERE = os.path.dirname(os.path.abspath(__file__))

SRC = os.path.join(_HERE, "catalog.md")
OUT = os.path.join(_HERE, "catalog.json")

text = open(SRC, encoding="utf-8").read()

def slugify(name):
    s = unicodedata.normalize("NFKD", name.lower())
    s = s.replace("&", "and").replace("+", "plus").replace(":", "")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s

tiers = {}
for m in re.finditer(r"^## (TIER [123]) — ([A-Z ]+?) \(\$(\d+)[–-]\$?(\d+)/mo\)", text, re.M):
    tiers[m.group(1)] = {"label": m.group(2).title().strip(), "start": m.start()}

# strategy blocks: "### N. Name — $X/mo" then meta line, optional desc paragraph, stat line
blocks = re.split(r"^### ", text, flags=re.M)[1:]
strategies = []
for b in blocks:
    lines = [l.strip() for l in b.strip().splitlines() if l.strip()]
    head = lines[0]
    hm = re.match(r"(\d+)\. (.+?) — \$(\d+)/mo", head)
    if not hm:
        continue
    num, name, price = int(hm.group(1)), hm.group(2).strip(), int(hm.group(3))
    # position → tier
    pos = text.find("### " + head)
    tier = None
    for tname, tinfo in tiers.items():
        if pos > tinfo["start"]:
            tier = tname
    # meta line: first non-parenthetical line after the header
    meta_idx = next(i for i, l in enumerate(lines[1:], 1) if not l.startswith("("))
    meta_line = lines[meta_idx]
    # stat line: last non-note line containing PF
    stat_line = None
    desc_lines = []
    for l in lines[meta_idx + 1:]:
        # a "---" rule or "##" heading marks the end of this entry's own content
        # (the final entry of each split block otherwise swallows the next sheet section)
        if l.startswith("---") or l.startswith("#"):
            break
        if l.startswith("("):
            continue
        if re.search(r"\bPF \d", l):
            stat_line = l
        else:
            desc_lines.append(l)
    stats = {}
    if stat_line:
        s = stat_line
        # NY Open Pro dual engines
        if "v1:" in s:
            stats["engines"] = {}
            for eng in re.finditer(r"(v\d): PF ([\d.]+) · Win (\d+)% · n=([\d,]+) · Net \$([\d,]+)", s):
                stats["engines"][eng.group(1)] = {
                    "pf": eng.group(2), "win": eng.group(3) + "%",
                    "n": eng.group(4), "net": "$" + eng.group(5),
                }
        else:
            for pat, key in [
                (r"PF ([\d.]+)", "pf"),
                (r"Win ([\d.]+)%", "win"),
                (r"n=([\d,]+)", "n"),
                (r"Net \$([\d,]+)", "net"),
                (r"MaxDD \$([\d,]+)", "maxdd"),
                (r"RoDD ([\d.]+)×", "rodd"),
            ]:
                mm = re.search(pat, s)
                if mm:
                    v = mm.group(1)
                    if key == "win": v += "%"
                    if key in ("net", "maxdd"): v = "$" + v
                    if key == "rodd": v += "\u00d7"
                    stats[key] = v
            if "small sample" in s:
                stats["note"] = "small sample \u2014 priced accordingly"
    # meta: **NQ · descriptor · status [· badge]**
    meta = meta_line.strip("*").strip()
    parts = [p.strip() for p in meta.split("\u00b7")]
    market = parts[0]
    status = next((p for p in parts if p.startswith(("TV-", "LIVE-"))), "")
    status = re.sub(r"\s*\(.*\)$", "", status)
    play = " \u00b7 ".join(p for p in parts[1:] if not p.startswith(("TV-", "LIVE-")))
    strategies.append({
        "num": num, "name": name, "slug": slugify(name), "price": price,
        "tier": tier, "tier_label": tiers[tier]["label"] if tier else "",
        "market": market, "play": play, "status": status,
        "desc": " ".join(desc_lines), "stats": stats,
    })

result = {
    "strategies": strategies,
    "bundles": [
        {"name": "The Books", "slug": "the-books", "price": 4999,
         "desc": "All four in-house engines. The metric that matters at this level: return on drawdown."},
        {"name": "All-Access", "slug": "all-access", "price": 999,
         "desc": "Every strategy, new releases included; menu value $3,400+."},
        {"name": "Pick-3", "slug": "pick-3", "price": 499,
         "desc": "Any three systems, swap monthly."},
    ],
    "annual_note": "Annual on anything = 2 months free",
    "delivery": "TradingView invite-only script, activated within 24h",
    "disclaimer": ("All performance figures are backtested or validation-run results at one-contract scale, "
                   "shown with commissions and slippage modeled. Backtested performance is hypothetical, does not "
                   "represent live trading results, and is not a guarantee or projection of future returns. Futures "
                   "trading involves substantial risk of loss and is not suitable for all investors. Nothing on this "
                   "site is financial advice. Access provides the strategy tool only; you are responsible for your "
                   "own trading decisions."),
}

json.dump(result, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print(f"parsed {len(strategies)} strategies")
for s in strategies:
    print(f"  {s['num']:>2} {s['slug']:<32} ${s['price']:<4} {s['tier']:<7} {s['status']:<15} stats={list(s['stats'].keys())}")
assert len(strategies) == 32, "expected 32 strategies"
assert strategies[22]["slug"] == "sydney-session-rider" and "win" not in strategies[22]["stats"], "Sydney must have no win%"
assert "engines" in strategies[1]["stats"], "NY Open Pro must have dual engines"
print("OK: 32 strategies, invariants hold")
