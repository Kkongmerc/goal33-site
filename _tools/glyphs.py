"""Per-product glyph library — one minimalistic mark per strategy, matched to
the display name, plus the four book emblems. Stroke-only, currentColor, so
each glyph inherits whatever text state surrounds it (muted at rest, amber on
row hover, book color inside the deck). Shared by rebuild_index.py, gen_plan.py."""

SW = 1.6  # stroke width for 24px strategy glyphs

# slug -> inner SVG content (24x24 viewBox, stroke=currentColor set on <svg>)
STRAT = {
    # Continuum — the 24h book: clock in orbit
    "continuum": '<circle cx="12" cy="12" r="8.6" stroke-dasharray="1.4 3.5" opacity=".6"/><circle cx="12" cy="12" r="5.4"/><path d="M12 12V8.6M12 12l2.6 1.8"/>',
    # Midas — the gold book: crown
    "midas": '<path d="M4.4 16.8 5.9 7.6l4 3.5L12 5.4l2.1 5.7 4-3.5 1.5 9.2z"/>'
             '<path d="M5.6 19.9h12.8"/>',
    # Aftershock — 08:30 data burst: seismograph
    "aftershock": '<path d="M3 14.5h3.4l2-8.2 3 12.4 2.4-9 1.6 4.8H21"/>',
    # Strongbox — three-leg book: banded chest
    "strongbox": '<rect x="4" y="7" width="16" height="12" rx="1.2"/><path d="M4 11h16"/><path d="M9 7v12M15 7v12" opacity=".6"/><circle cx="12" cy="14.8" r="1.5"/>',
    # Slipstream — FVG continuation: layered flow
    # Ignition - the 09:30 open lighting the session: flame
    "ignition": '<path d="M12 3.4c-.5 2.5-2 3.8-3.4 5.3-1.5 1.6-2.4 3.2-2.4 5.2a5.8 5.8 0 0 0 11.6 0c0-2.5-1.3-4.3-2.9-6-1.2-1.3-2.4-2.6-2.9-4.5z"/>'
                '<path d="M12 12.6c-1 1.3-2 2.2-2 3.6a2 2 0 0 0 4 0c0-1.4-1-2.3-2-3.6z"/>',
    "slipstream": '<path d="M3.5 8h11a2.8 2.8 0 1 0-2.6-3.8"/><path d="M3.5 12.5H18a3 3 0 1 1-2.8 4"/><path d="M3.5 17h7"/>',
    # The Alloy (slug tailwind) — two metals fused: overlapping ingot diamonds
    "tailwind": '<path d="M8.5 5.5 13 10l-4.5 4.5L4 10z"/><path d="M15.5 9.5 20 14l-4.5 4.5L11 14z"/>',
    # Headline Risk (slug relay) — front page
    "relay": '<rect x="4" y="5" width="16" height="14" rx="1"/><rect x="7" y="8" width="5.6" height="4"/><path d="M15.4 8.8h1.8M15.4 11.4h1.8M7 15.8h10"/>',
    # The Press (slug undertow) — beam, ram, plate, work, base
    "undertow": '<path d="M4.5 4h15"/><path d="M12 4v5"/><path d="M8 9h8"/><path d="M9.8 13.5h4.4v2.6H9.8z"/><path d="M4.5 20h15"/>',
    # The Pendulum (slug meridian) — pivot, rod, bob, swing arc
    "meridian": '<circle cx="12" cy="4.4" r="1.1"/><path d="M12 5.4 16.6 15"/><circle cx="17.6" cy="17.2" r="2.5"/><path d="M6 14.6a10 10 0 0 0 4 4.2"/>',
    # Counterweight (slug closer) — kettlebell
    "closer": '<circle cx="12" cy="14.2" r="5.3"/><path d="M8.9 10.1a4.4 4.4 0 0 1 6.2 0"/>',
    # Lantern — 20:00 Tokyo open fade: paper lantern, ribbed body
    "lantern": '<path d="M12 2.4v2.4"/><path d="M8 6.4h8"/><path d="M7.6 6.9 8.7 17a3.3 3.3 0 0 0 6.6 0l1.1-10.1z"/><path d="M8.3 15h7.4M9 10.6h6"/><path d="M12 19.6v2"/>',
    # First Light — 19:00 Sydney open drive: sunrise over the horizon
    "first-light": '<path d="M3.6 15.5h16.8"/><path d="M6.8 15.5a5.2 5.2 0 0 1 10.4 0"/><path d="M12 6v2.4M6.6 9.2l1.7 1.5M17.4 9.2l-1.7 1.5"/>',
    # Undercurrent — 08:30 fade, Tue/Thu: the surface wave and the one beneath it
    "undercurrent": '<path d="M3.4 10.4c2-3.6 4.3-3.6 6.3 0s4.3 3.6 6.3 0 3-3.2 3.6-2.1" opacity=".55"/><path d="M3.4 15.4c2-3.6 4.3-3.6 6.3 0s4.3 3.6 6.3 0 3-3.2 3.6-2.1"/>',
    # Confluence — two legs merging into one: converging arrows
    "confluence": '<path d="M4 5.4 11 12l-7 6.6"/><path d="M20 5.4 13 12l7 6.6"/><circle cx="12" cy="12" r="1.3"/>',
    # The Night Shift (slug daybreak) — crescent moon with a star
    "daybreak": '<path d="M14.8 3.6a8.4 8.4 0 1 0 5.6 13.9A8.4 8.4 0 0 1 14.8 3.6z"/><path d="M5.6 5.8v2.6M4.3 7.1h2.6" opacity=".7"/>',
    # The Assay (slug assay) — the assayer's flask
    # The Assay / The Kilo / The Print — the MGC leg slugs on the site carry the article
    # Triad — three legs, one script: a triangle of three nodes
    "triad": '<path d="M12 4.6 19.4 18H4.6z"/><circle cx="12" cy="4.6" r="1.4"/><circle cx="4.6" cy="18" r="1.4"/><circle cx="19.4" cy="18" r="1.4"/>',
    "the-assay": '<path d="M10 4h4"/><path d="M11 4v5.2L6.2 17a2.4 2.4 0 0 0 2.1 3.6h7.4a2.4 2.4 0 0 0 2.1-3.6L13 9.2V4"/><path d="M8.2 14.5h7.6"/>',
    "the-kilo": '<path d="M7.2 9h9.6l2.7 7.8H4.5z"/><path d="M9.3 6.2h5.4l1 2.8H8.3z" opacity=".65"/>',
    "the-print": '<rect x="4" y="8" width="16" height="5" rx="1"/><path d="M8 13v6h8v-6"/><path d="M10 15.5h4M10 17.5h2.6"/><path d="M7 8V5h10v3"/>',
    # The Fix — the London fix: a bell over the fix line
    "the-fix": '<path d="M12 3.6v1.6"/><path d="M7.4 14.2V10a4.6 4.6 0 0 1 9.2 0v4.2l1.6 2.2H5.8z"/><path d="M10.2 18.8a1.8 1.8 0 0 0 3.6 0"/><path d="M4 21h16" opacity=".6"/>',
    # The Ingot — a cast gold bar (unlisted until its standalone matches the book leg)
    # The Books (combined row) — two volumes side by side
    "the-books": '<path d="M5 4h5.5v16H5z"/><path d="M13.5 4H19v16h-5.5z"/><path d="M7 8h1.5M16 8h1.5M7 12h1.5M16 12h1.5" opacity=".6"/>',
    "the-ingot": '<path d="M6.5 8.5h11l2.5 8h-16z"/><path d="M8.6 8.5 9.4 16.5M15.4 8.5l-.8 8" opacity=".55"/>',
    "assay": '<path d="M10 4h4"/><path d="M11 4v5.2L6.2 17a2.4 2.4 0 0 0 2.1 3.6h7.4a2.4 2.4 0 0 0 2.1-3.6L13 9.2V4"/><path d="M8.2 14.5h7.6"/>',
    # The Kilo (slug kilo) — stacked gold kilobars
    "kilo": '<path d="M7.2 9h9.6l2.7 7.8H4.5z"/><path d="M9.3 6.2h5.4l1 2.8H8.3z" opacity=".65"/>',
    # The Print (slug print) — the data print coming off the wire
    "print": '<rect x="4" y="8" width="16" height="5" rx="1"/><path d="M8 13v6h8v-6"/><path d="M10 15.5h4M10 17.5h2.6"/><path d="M7 8V5h10v3"/>',
    # The Fix (slug greenwich) — the balance scale of the London fix
    "greenwich": '<path d="M12 4.2v13.3"/><path d="M9 19.5h6"/><path d="M5.5 7h13"/><path d="M5.5 7 3.4 11.4M5.5 7l2.1 4.4"/><path d="M2.8 11.4a2.7 2.7 0 0 0 5.4 0z"/><path d="M18.5 7l-2.1 4.4M18.5 7l2.1 4.4"/><path d="M15.8 11.4a2.7 2.7 0 0 0 5.4 0z"/>',
    # Spartacus — gladiator helm: dome, T-visor, crest
    "spartacus": '<path d="M6 20v-7a6 6 0 0 1 12 0v7"/><path d="M12 10v10"/><path d="M7.5 13.5h9"/><path d="M8 4.2c2.6-1.9 5.4-1.9 8 0"/>',
    # The Alloy — two metals fused: overlapping ingot diamonds
    "the-alloy": '<path d="M8.5 5.5 13 10l-4.5 4.5L4 10z"/><path d="M15.5 9.5 20 14l-4.5 4.5L11 14z"/>',
    # Sterling — silver ingot with a hallmark spark
    "silver-830-reversal": '<path d="M7.5 9.5h9l2.6 7.5H4.9z"/><path d="M17 3.6v3.2"/><path d="M15.4 5.2h3.2"/>',
    # The Abacus — frame, divider, beads
    "china-orb": '<rect x="4" y="5" width="16" height="14" rx="1"/><path d="M4 10.4h16"/><circle cx="8.6" cy="7.7" r="1.15"/><circle cx="13" cy="7.7" r="1.15"/><circle cx="9.4" cy="14.7" r="1.15"/><circle cx="14.6" cy="14.7" r="1.15"/>',
    # The Pendulum — pivot, rod, bob, swing arc
    "afternoon-reversion": '<circle cx="12" cy="4.4" r="1.1"/><path d="M12 5.4 16.6 15"/><circle cx="17.6" cy="17.2" r="2.5"/><path d="M6 14.6a10 10 0 0 0 4 4.2"/>',
    # The Press — beam, ram, plate, work, base
    "30m-structure-reclaim": '<path d="M4.5 4h15"/><path d="M12 4v5"/><path d="M8 9h8"/><path d="M9.8 13.5h4.4v2.6H9.8z"/><path d="M4.5 20h15"/>',
    # Counterweight — kettlebell
    "es-pullback-fade": '<circle cx="12" cy="14.2" r="5.3"/><path d="M8.9 10.1a4.4 4.4 0 0 1 6.2 0"/>',
    # Lunch Money — banknote
    "lunch-break-fade": '<rect x="3.5" y="7" width="17" height="10" rx="1"/><circle cx="12" cy="12" r="2.5"/><path d="M6.6 10.6v2.8M17.4 10.6v2.8"/>',
    # Mean Machine — the mean line and the wave that snaps back to it
    "vwap-band-fade": '<path d="M3 12h2.2M8 12h2.2M13 12h2.2M18 12h2.2" opacity=".55"/><path d="M3.5 12c2.1-5.4 4.6-5.4 6.7 0s4.6 5.4 6.7 0 3.1-4 3.6-2.6"/>',
    # Argent — cut gem
    "silver-midday-range-fade": '<path d="M12 4.5 18 10l-6 9.5L6 10z"/><path d="M6.6 10h10.8"/><path d="M9.6 10 12 4.5 14.4 10"/>',
    # The Weekender — calendar, Friday marked
    "friday-orb": '<rect x="4" y="6" width="16" height="13.5" rx="1"/><path d="M8.4 3.8V8M15.6 3.8V8"/><path d="M4 10.6h16"/><circle cx="15.7" cy="15.9" r="1.5"/>',
    # Aftershock — seismograph spike train
    "830-range-fade": '<path d="M3 14.5h3.4l2-8.2 3 12.4 2.4-9 1.6 4.8H21"/>',
    # Autobahn — lanes converging, dashed centerline
    "frankfurt-continuation": '<path d="M7.6 20 11.2 4M16.4 20 12.8 4"/><path d="M12 18.4v-2.4M12 12.9v-2.4M12 7.4V5.4" opacity=".7"/>',
    # The Collector — coin jar
    "pool-milestone-pullback": '<path d="M8.6 4h6.8v2.6c2 1.7 2.6 3.2 2.6 5.6a6 6 0 0 1-12 0c0-2.4.6-3.9 2.6-5.6z"/><circle cx="10.6" cy="13.4" r="1.3"/><circle cx="13.7" cy="15.6" r="1.3"/>',
    # Headline Risk — front page
    "830-news-fade": '<rect x="4" y="5" width="16" height="14" rx="1"/><rect x="7" y="8" width="5.6" height="4"/><path d="M15.4 8.8h1.8M15.4 11.4h1.8M7 15.8h10"/>',
    # The Grip — bar with finger hooks
    "1030-fade": '<path d="M4 14.6h16"/><path d="M7 14.6v-2.6a1.5 1.5 0 0 1 3 0v2.6M10.5 14.6v-3.2a1.5 1.5 0 0 1 3 0v3.2M14 14.6v-2.6a1.5 1.5 0 0 1 3 0v2.6"/>',
    # The Clamp — jaws closing on the mark
    "the-vise": '<path d="M7.5 5v14M7.5 5h3.6M7.5 19h3.6"/><path d="M16.5 5v14M16.5 5h-3.6M16.5 19h-3.6"/><circle cx="12" cy="12" r="1.4"/>',
    # The Clamp 25pt — same jaws, wider bite
    "the-vise-25": '<path d="M6.5 5v14M6.5 5h3.4M6.5 19h3.4"/><path d="M17.5 5v14M17.5 5h-3.4M17.5 19h-3.4"/><circle cx="10.5" cy="12" r="1.25"/><circle cx="13.5" cy="12" r="1.25"/>',
    # The Vise — C-clamp with screw
    "cme-reopen-snap": '<path d="M15.8 5.2a7.2 7.2 0 1 0 0 13.6"/><path d="M15.8 5.2h3.4M15.8 18.8h3.4"/><path d="M19.4 8.4v7.2"/><path d="M17.6 8.4h3.6"/>',
    # The Market Maker — the exchange facade
    "ny-open-pro": '<path d="M4 9.4 12 4l8 5.4"/><path d="M6.4 9.4v7.2M12 9.4v7.2M17.6 9.4v7.2"/><path d="M4.5 19.6h15"/>',
}

# book slug -> (inner SVG, 48x48 viewBox) — drawn larger, animated via CSS classes
BOOK = {
    # The Midas — crown with rays and gems
    "the-midas": ('<g class="bk-art"><path d="M9 33.5 12.5 17l7.5 7.5L24 12l4 12.5L35.5 17 39 33.5z"/>'
                  '<path d="M9 37.5h30"/>'
                  '<path class="bk-ray" d="M24 4.5v4M12.8 7.2l2 3M35.2 7.2l-2 3"/>'
                  '<circle cx="16" cy="29.5" r="1.2"/><circle cx="24" cy="28.5" r="1.2"/><circle cx="32" cy="29.5" r="1.2"/></g>'),
    # The Continuum — clock inside a slow orbit
    "the-continuum": ('<g class="bk-art"><circle cx="24" cy="24" r="19" stroke-dasharray="2.4 5.2" opacity=".55"/>'
                      '<circle cx="24" cy="24" r="11.5"/>'
                      '<path d="M24 24V16M24 24l5.4 3.6"/>'
                      '<path d="M24 13.4v1.8M34.6 24h-1.8M24 34.6v-1.8M13.4 24h1.8" opacity=".7"/>'
                      '<g class="bk-orbit"><circle cx="24" cy="5" r="2"/></g></g>'),
    # The Daylight — sun at full rays
    "the-daylight": ('<g class="bk-art"><circle cx="24" cy="24" r="8"/>'
                     '<g class="bk-rays"><path d="M24 4.5v5.5M24 38v5.5M4.5 24H10M38 24h5.5M10.2 10.2l3.9 3.9M33.9 33.9l3.9 3.9M37.8 10.2l-3.9 3.9M14.1 33.9l-3.9 3.9"/></g></g>'),
    # The Vault — door wheel and bolt ring
    "the-ledger": ('<g class="bk-art"><circle cx="24" cy="24" r="18.5"/>'
                   '<circle cx="24" cy="24" r="14.5" stroke-dasharray="1.6 6.05" opacity=".6"/>'
                   '<g class="bk-wheel"><circle cx="24" cy="24" r="7"/>'
                   '<path d="M24 13.5v21M14.9 18.75l18.2 10.5M33.1 18.75l-18.2 10.5"/></g></g>'),
}


def glyph(slug, cls="glyph"):
    """16-24px strategy mark; sized by the CSS class."""
    inner = STRAT.get(slug)
    if not inner:
        return ""
    return (f'<svg class="{cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{inner}</svg>')


def emblem(slug, cls="bk-emblem"):
    """Book emblem, 48x48."""
    inner = BOOK.get(slug)
    if not inner:
        return ""
    return (f'<svg class="{cls}" viewBox="0 0 48 48" fill="none" stroke="currentColor" '
            f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{inner}</svg>')
