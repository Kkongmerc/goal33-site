"""Deterministic illustrative equity paths fitted to published stats.
For each system: simulate n trades at the published win%/PF, pick the seeded run whose
drawdown/net ratio best matches the published MaxDD, scale so the curve ends exactly
at the published Net. Output SVG path data. NOT real trade data — labeled as such on-page."""
import random

VB_W, VB_H = 640, 180
PAD_X, PAD_T, PAD_B = 6, 10, 8
N_POINTS = 120

def _num(s):
    return float(str(s).replace("$", "").replace(",", "").replace("%", ""))

def _simulate(seed, n, p_win, w_ratio):
    rng = random.Random(seed)
    cum, y = [0.0], 0.0
    for _ in range(n):
        size = rng.uniform(0.45, 1.75)
        y += w_ratio * size if rng.random() < p_win else -size
        cum.append(y)
    return cum

def _maxdd(cum):
    peak, dd = cum[0], 0.0
    for v in cum:
        peak = max(peak, v)
        dd = max(dd, peak - v)
    return dd

def series(slug, net, n=None, win=None, pf=None, maxdd=None):
    """Return list of N_POINTS floats ending exactly at `net` (dollars)."""
    net_v = _num(net)
    n_t = int(_num(n)) if n else 160
    n_t = max(40, min(n_t, 1200))
    p = (_num(win) / 100.0) if win else 0.5
    pf_v = _num(pf) if pf else 1.5
    w_ratio = pf_v * (1 - p) / max(p, .05)
    target_ratio = (_num(maxdd) / net_v) if (maxdd and net_v > 0) else 0.18
    best, best_score = None, None
    for k in range(240):
        cum = _simulate(f"{slug}:{k}", n_t, p, w_ratio)
        if cum[-1] <= 0:
            continue
        s = net_v / cum[-1]
        ratio = (_maxdd(cum) * s) / net_v
        score = abs(ratio - target_ratio)
        if best_score is None or score < best_score:
            best, best_score = [v * net_v / cum[-1] for v in cum], score
    # downsample to N_POINTS
    cum = best
    step = (len(cum) - 1) / (N_POINTS - 1)
    return [cum[round(i * step)] for i in range(N_POINTS)]

def to_paths(all_series, vb_w=VB_W, vb_h=VB_H):
    """all_series: list of float-lists sharing one y-scale. Returns (line_paths, area_paths, y_zero)."""
    lo = min(min(s) for s in all_series + [[0]])
    hi = max(max(s) for s in all_series)
    span = (hi - lo) or 1
    inner_h = vb_h - PAD_T - PAD_B
    inner_w = vb_w - 2 * PAD_X
    def Y(v): return PAD_T + (hi - v) / span * inner_h
    lines, areas = [], []
    for s in all_series:
        pts = [(PAD_X + i * inner_w / (len(s) - 1), Y(v)) for i, v in enumerate(s)]
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        lines.append(d)
        areas.append(d + f" L{pts[-1][0]:.1f} {vb_h - PAD_B} L{pts[0][0]:.1f} {vb_h - PAD_B} Z")
    return lines, areas, Y(0)
