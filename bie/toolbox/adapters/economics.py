"""Economics computed in Python for BIE's chart blocks (Task 046a, batch 3); the data comes from the World Bank through
``bie.toolbox.sources.world_bank``.

- ``cobb_douglas``: output Q = A·K^α·L^β on a grid of capital and labour, the isoquants to draw, and the cost-minimising
  expansion path for given input prices (K/L = (α/β)·(w/r)), with the returns to scale.
- ``joined_frames``: several World Bank indicators joined country by country and year by year (a value missing inside
  a country's range is filled by straight-line interpolation and marked), for a chart that moves through the years.
"""
from __future__ import annotations

from .base import clean, need


def cobb_douglas(*, A: float = 1.0, alpha: float = 0.4, beta: float = 0.6, k_max: float = 100.0, l_max: float = 100.0,
                 n: int = 41, levels=(10, 20, 30, 40, 50, 60, 70), r: float = 2.0, w: float = 1.0) -> dict:
    np = need("numpy")
    k = np.linspace(0, k_max, n)
    l = np.linspace(0, l_max, n)
    K, L = np.meshgrid(k, l)
    Q = A * K ** alpha * L ** beta
    ratio = (alpha / beta) * (w / r)                     # cost-minimising K/L from the tangency of isoquant and isocost
    path = [[float(lab * ratio), float(lab), float(A * (lab * ratio) ** alpha * lab ** beta)] for lab in np.linspace(0, l_max, 21)
            if lab * ratio <= k_max]
    return clean({"K": k, "L": l, "Q": Q, "levels": list(levels), "A": A, "alpha": alpha, "beta": beta, "r": r, "w": w,
                  "k_over_l": ratio, "returns_to_scale": "constant" if abs(alpha + beta - 1) < 1e-9 else
                  ("increasing" if alpha + beta > 1 else "decreasing"), "expansion_path": path,
                  "computed_by": f"NumPy {np.__version__}"}, 3)


def joined_frames(series: dict, years, *, names: dict | None = None) -> dict:
    """``series`` maps a key (``x``, ``y``, ``size``) to World Bank rows; returns one frame per year with every country
    that has all keys at that year (interpolated inside the country's own range, never extrapolated)."""
    np = need("numpy")
    keys = list(series)
    by = {k: {} for k in keys}
    for k, rows in series.items():
        for r in rows:
            by[k].setdefault(r["iso3"], {})[r["year"]] = r["value"]
    countries = sorted(set.intersection(*[set(by[k]) for k in keys]))
    names = names or {r["iso3"]: r["country"] for rows in series.values() for r in rows}
    frames = []
    for year in years:
        points = []
        for iso in countries:
            row, filled = {"iso3": iso, "country": names.get(iso, iso)}, False
            for k in keys:
                known = by[k][iso]
                if year in known:
                    row[k] = known[year]
                    continue
                ys = sorted(known)
                if not ys or year < ys[0] or year > ys[-1]:
                    row = None
                    break
                row[k] = float(np.interp(year, ys, [known[y] for y in ys]))
                filled = True
            if row is not None:
                row["interpolated"] = filled
                points.append(row)
        frames.append({"year": year, "points": points})
    return clean({"keys": keys, "countries": countries, "frames": frames}, 3)
