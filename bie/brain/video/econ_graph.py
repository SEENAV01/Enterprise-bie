"""Economics graphs from their economics, not from hand-placed points (the Sloman book, 5 November 2026).

The graph saancha draws lines from data points. A director that writes those points by hand gets the arithmetic wrong:
the equilibrium dot misses the crossing, the surplus triangle misses the curve, the tax wedge is not the tax (EV-L03,
EV-R01: every derived number agrees with the example). This builder takes the economics — a demand P = a - bQ, a supply,
a cost curve as a function, a tax, a ceiling — and computes every point, crossing and area, so the drawing and the
numbers spoken always agree. It returns the graph saancha's parameters (and its steps), written in the plan language.

    g = EconGraph(xmax=10, ymax=10, x_label="मात्रा", y_label="कीमत")
    D = g.linear("D", intercept=9, slope=-0.8)          # P = 9 - 0.8 Q
    S = g.linear("S", intercept=1, slope=0.8)
    E = g.cross(D, S, "E")                               # the equilibrium point, computed
    g.surplus_consumer(D, E, "उपभोक्ता बचत")
    D2 = g.shift(D, dx=2, name="D2")                     # demand rises: the whole curve moves right
    g.arrow_between(D, D2, at_y=6, label="माँग बढ़ी")
    p = g.params(show=[D, S])                            # the first state; later states are item steps

Beyond the market diagram (every helper computes its points from the economics):
    consumer choice   budget(), indifference(), best_bundle(), compensated() (substitution and income effects), touch()
    national income   forty_five(), staircase() (the multiplier's rounds; also a cobweb between demand and supply)
    the firm          marginal(), average(), revenue_marginal() from a total function
    scarcity          ppf() (bowed or straight), tangent() for the opportunity cost
    distribution      lorenz() from group shares (its Gini in line.meta), piecewise() for any kinked line
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass(eq=False)
class Line:
    name: str
    f: object                       # P = f(Q): a callable over the x range
    color: str = ""
    dashed: bool = False
    domain: tuple = ()               # (x0, x1) to draw over; the whole range by default
    index: int = 0                   # 1-based place in the saancha's lines
    xs: tuple = ()                   # the x values to sample at (a bending curve wants them closer where it bends)
    meta: dict = field(default_factory=dict)   # what the economics knows about the line (income, prices, utility, Gini)


@dataclass
class Point:
    x: float
    y: float
    name: str = ""
    u: float = 0.0                   # the utility at a best bundle (best_bundle)


def _fmt(v: float) -> str:
    r = round(v, 2)
    return str(int(r)) if r == int(r) else f"{r:g}"


@dataclass
class EconGraph:
    xmax: float = 10.0
    ymax: float = 10.0
    xmin: float = 0.0
    ymin: float = 0.0
    x_label: str = ""
    y_label: str = ""
    title: str = ""
    w: int = 1200
    samples: int = 9
    smooth: bool = True              # False: lines are straight between their points (a kinked demand curve)
    lines: list = field(default_factory=list)
    areas: list = field(default_factory=list)
    dots: list = field(default_factory=list)
    hlines: list = field(default_factory=list)
    vlines: list = field(default_factory=list)
    arrows: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    xticks: list = field(default_factory=list)
    yticks: list = field(default_factory=list)
    segs: list = field(default_factory=list)
    path: list = field(default_factory=list)

    # ------------------------------------------------------------------ curves
    def curve(self, name: str, f, *, color: str = "", dashed: bool = False, domain: tuple = (), xs: tuple = ()) -> Line:
        """Any P = f(Q) (a cost curve, an indifference curve solved for y, a Lorenz curve): sampled smoothly."""
        if len(self.lines) >= 6:
            raise ValueError("the graph saancha draws at most six lines; split the idea over two graphs")
        line = Line(name, f, color, dashed, domain, len(self.lines) + 1, tuple(xs))
        self.lines.append(line)
        return line

    def linear(self, name: str, *, intercept: float, slope: float, **kw) -> Line:
        """A straight line P = intercept + slope * Q (demand: slope < 0; supply: slope > 0)."""
        return self.curve(name, lambda q, a=intercept, b=slope: a + b * q, **kw)

    def through(self, name: str, p1: tuple, p2: tuple, **kw) -> Line:
        """A straight line through two (Q, P) points."""
        (x1, y1), (x2, y2) = p1, p2
        if x1 == x2:
            raise ValueError("a vertical line: use vertical() (perfectly inelastic supply) or vline() (a dashed marker)")
        slope = (y2 - y1) / (x2 - x1)
        return self.linear(name, intercept=y1 - slope * x1, slope=slope, **kw)

    def vertical(self, name: str, x: float, *, y0: float | None = None, y1: float | None = None, color: str = "",
                 dashed: bool = False) -> Line:
        """A vertical curve Q = x (perfectly inelastic supply, a fixed stock, the long-run Phillips curve): one of the
        graph's lines, drawn solid from y0 to y1 (the whole height by default). cross() and at_price() know it."""
        if not self.xmin <= x <= self.xmax:
            raise ValueError(f"the vertical line Q = {x:g} lies outside the frame")
        lo = self.ymin if y0 is None else y0
        hi = self.ymax if y1 is None else y1

        def f(q, x=x):
            raise ValueError("a vertical line has no single price at a quantity; use cross() or at_price()")
        line = self.curve(name, f, color=color, dashed=dashed)
        line.meta["vertical"] = (float(x), float(lo), float(hi))
        return line

    def shift(self, line: Line, *, dx: float = 0.0, dy: float = 0.0, name: str = "", dashed: bool = True,
              color: str = "") -> Line:
        """The same curve moved: dx > 0 moves it right (more is bought or sold at every price), dy > 0 up (a tax on
        the sellers lifts supply by the tax)."""
        if "vertical" in line.meta:
            x, lo, hi = line.meta["vertical"]
            return self.vertical(name or line.name + "2", x + dx, y0=lo + dy, y1=hi + dy, color=color, dashed=dashed)
        return self.curve(name or line.name + "2", lambda q, f=line.f: f(q - dx) + dy, dashed=dashed, color=color,
                          domain=tuple(v + dx for v in line.domain) if line.domain else (),
                          xs=tuple(v + dx for v in line.xs))

    # ------------------------------------------------------------------ what the economics computes
    def value(self, line: Line, q: float) -> float:
        return float(line.f(q))

    def cross(self, a: Line, b: Line, name: str = "", *, dot: bool = True) -> Point:
        """Where two curves meet (bisection on the difference over the x range): the equilibrium, MC = MR, AD = AS."""
        if "vertical" in a.meta or "vertical" in b.meta:
            v, o = (a, b) if "vertical" in a.meta else (b, a)
            if "vertical" in o.meta:
                raise ValueError(f"{a.name} and {b.name} are both vertical")
            x = v.meta["vertical"][0]
            p = Point(round(x, 4), round(float(o.f(x)), 4), name)
            if dot:
                self.dots.append(p)
            return p
        g = lambda q: a.f(q) - b.f(q)  # noqa: E731
        lo, hi = self.xmin, self.xmax
        n = 400
        prev_q, prev_v = lo, g(lo)
        for i in range(1, n + 1):
            q = lo + (hi - lo) * i / n
            v = g(q)
            if prev_v == 0:
                q, v = prev_q, 0.0
                break
            if prev_v * v <= 0:
                x0, x1 = prev_q, q
                for _ in range(60):
                    m = (x0 + x1) / 2
                    if g(x0) * g(m) <= 0:
                        x1 = m
                    else:
                        x0 = m
                q = (x0 + x1) / 2
                break
            prev_q, prev_v = q, v
        else:
            raise ValueError(f"{a.name} and {b.name} do not meet between {lo} and {hi}")
        p = Point(round(q, 4), round(float(a.f(q)), 4), name)
        if dot:
            self.dots.append(p)
        return p

    def at_price(self, line: Line, price: float) -> float:
        """The quantity on a curve at a price (demand or supply at a ceiling or a floor)."""
        if "vertical" in line.meta:
            return line.meta["vertical"][0]
        flat = Line("", lambda q, c=price: c)
        return self.cross(line, flat, dot=False).x

    # ------------------------------------------------------------------ the marks
    def dot(self, x: float, y: float, name: str = "", *, glide_from: Point | None = None) -> Point:
        p = Point(x, y, name)
        p.glide_from = glide_from               # type: ignore[attr-defined]
        self.dots.append(p)
        return p

    def hline(self, y: float, label: str = ""):
        self.hlines.append((y, label))

    def vline(self, x: float, label: str = ""):
        self.vlines.append((x, label))

    def tick_x(self, x: float, label: str):
        self.xticks.append((x, label))

    def tick_y(self, y: float, label: str):
        self.yticks.append((y, label))

    def arrow(self, p1: tuple, p2: tuple, label: str = ""):
        self.arrows.append((p1, p2, label))

    def arrow_between(self, a: Line, b: Line, *, at_y: float, label: str = ""):
        """A shift arrow from curve a to curve b at one price."""
        self.arrows.append(((self.at_price(a, at_y), at_y), (self.at_price(b, at_y), at_y), label))

    def seg(self, p1: tuple, p2: tuple, label: str = ""):
        """A dashed segment: a chord, a tangent, a reading line."""
        self.segs.append((p1, p2, label))

    def tangent(self, line: Line, q: float, *, half: float = 1.5, label: str = "") -> float:
        """The tangent of a curve at q (its slope by a small difference), drawn as a dashed segment; returns the slope."""
        e = 1e-4 * max(1.0, abs(self.xmax - self.xmin))
        k = (float(line.f(q + e)) - float(line.f(q - e))) / (2 * e)
        y = float(line.f(q))
        self.seg((q - half, y - k * half), (q + half, y + k * half), label)
        return k

    def path_points(self, points: list):
        """A lettered adjustment path: [(x, y, "a"), (x, y, "b"), …]."""
        self.path = list(points)

    def gap(self, x1: float, x2: float, at_y: float, label: str = ""):
        self.gaps.append((x1, x2, at_y, label))

    def area(self, points: list, label: str = "", color: str = "") -> int:
        """A shaded polygon of (Q, P) points; returns its 1-based number (grow "a<n>")."""
        self.areas.append((points, label, color))
        return len(self.areas)

    def under(self, line: Line, x0: float, x1: float, *, floor: float, label: str = "", color: str = "") -> int:
        """The area between a curve and a price from x0 to x1 (consumer surplus: demand above the price)."""
        n = max(2, self.samples)
        top = [(x0 + (x1 - x0) * i / n, float(line.f(x0 + (x1 - x0) * i / n))) for i in range(n + 1)]
        return self.area(top + [(x1, floor), (x0, floor)], label, color)

    def surplus_consumer(self, demand: Line, at: Point, label: str = "", color: str = "#f4a261") -> int:
        return self.under(demand, self.xmin, at.x, floor=at.y, label=label, color=color)

    def surplus_producer(self, supply: Line, at: Point, label: str = "", color: str = "#2a9d8f") -> int:
        n = max(2, self.samples)
        bottom = [(self.xmin + (at.x - self.xmin) * i / n, float(supply.f(self.xmin + (at.x - self.xmin) * i / n)))
                  for i in range(n + 1)]
        return self.area([(self.xmin, at.y), (at.x, at.y)] + list(reversed(bottom)), label, color)

    def rect(self, x0: float, x1: float, y0: float, y1: float, label: str = "", color: str = "") -> int:
        """A rectangle: tax revenue, total revenue P x Q, profit (P - AC) x Q."""
        return self.area([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], label, color)

    def triangle_between(self, a: Line, b: Line, x0: float, x1: float, label: str = "", color: str = "#e76f51") -> int:
        """The region between two curves from x0 to x1 (deadweight loss between demand and supply)."""
        n = max(2, self.samples)
        xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
        return self.area([(x, float(a.f(x))) for x in xs] + [(x, float(b.f(x))) for x in reversed(xs)], label, color)

    # ------------------------------------------------------------------ consumer choice
    def budget(self, name: str, *, income: float, px: float, py: float, **kw) -> Line:
        """The budget line px·X + py·Y = income, from (0, income/py) to (income/px, 0)."""
        if min(income, px, py) <= 0:
            raise ValueError("a budget line needs a positive income and positive prices")
        line = self.curve(name, lambda x, m=income, a=px, b=py: (m - a * x) / b,
                          domain=(self.xmin, min(self.xmax, income / px)), **kw)
        line.meta = {"income": income, "px": px, "py": py}
        return line

    def indifference(self, name: str, *, u: float, a: float = 0.5, **kw) -> Line:
        """An indifference curve of U = X^a · Y^(1-a) at utility u: convex to the origin, never touching an axis.
        Drawn only where it is inside the frame, with its points closer together where it bends."""
        if not 0 < a < 1 or u <= 0:
            raise ValueError("an indifference curve needs 0 < a < 1 and a positive utility")
        f = lambda x, u=u, a=a: (u / x ** a) ** (1 / (1 - a))  # noqa: E731
        lo = max(self.xmin, (u / self.ymax ** (1 - a)) ** (1 / a), 1e-6)
        hi = self.xmax
        if lo >= hi:
            raise ValueError(f"the indifference curve u = {u:g} lies outside the frame")
        n = max(2, self.samples)
        line = self.curve(name, f, domain=(lo, hi), xs=tuple(lo * (hi / lo) ** (i / n) for i in range(n + 1)), **kw)
        line.meta = {"u": u, "a": a}
        return line

    def best_bundle(self, budget: Line, *, a: float = 0.5, name: str = "", dot: bool = True) -> Point:
        """The consumer's best point on a budget line for U = X^a · Y^(1-a): X = a·M/px, Y = (1-a)·M/py. The point's
        u is the utility there, so indifference(u=point.u, a=a) is the curve that just touches the budget line."""
        m, px, py = (budget.meta[k] for k in ("income", "px", "py"))
        x, y = a * m / px, (1 - a) * m / py
        p = Point(round(x, 4), round(y, 4), name, x ** a * y ** (1 - a))
        if dot:
            self.dots.append(p)
        return p

    def compensated(self, name: str, new_budget: Line, *, u: float, a: float = 0.5, **kw) -> tuple:
        """The dashed budget line with the NEW prices that just reaches the OLD indifference curve (utility u), and
        its touching point. Old best bundle → this point is the substitution effect (along the old curve); this
        point → the new best bundle is the income effect."""
        px, py = new_budget.meta["px"], new_budget.meta["py"]
        x = u * (a / (1 - a) * py / px) ** (1 - a)
        y = u * ((1 - a) / a * px / py) ** a
        kw.setdefault("dashed", True)
        line = self.budget(name, income=px * x + py * y, px=px, py=py, **kw)
        return line, Point(round(x, 4), round(y, 4), "", u)

    def touch(self, a: Line, b: Line, name: str = "", *, dot: bool = True) -> Point:
        """Where curve a comes closest to curve b: a tangency (an isoquant on an isocost line, an indifference
        curve of any shape on a budget line)."""
        lo = max((a.domain or (self.xmin,))[0], (b.domain or (self.xmin,))[0])
        hi = min((a.domain or (0, self.xmax))[1], (b.domain or (0, self.xmax))[1])
        if lo >= hi:
            raise ValueError(f"{a.name} and {b.name} share no range")
        gap = lambda q: abs(float(a.f(q)) - float(b.f(q)))  # noqa: E731
        n = 2000
        k = min(range(n + 1), key=lambda i: gap(lo + (hi - lo) * i / n))
        x0, x1 = lo + (hi - lo) * max(0, k - 1) / n, lo + (hi - lo) * min(n, k + 1) / n
        for _ in range(60):
            m1, m2 = x0 + (x1 - x0) / 3, x1 - (x1 - x0) / 3
            if gap(m1) < gap(m2):
                x1 = m2
            else:
                x0 = m1
        q = (x0 + x1) / 2
        p = Point(round(q, 4), round(float(a.f(q)), 4), name)
        if dot:
            self.dots.append(p)
        return p

    # ------------------------------------------------------------------ national income
    def forty_five(self, name: str = "45°", **kw) -> Line:
        """The 45° line of the income–expenditure diagram: expenditure equal to income."""
        return self.linear(name, intercept=0, slope=1, **kw)

    def staircase(self, a: Line, b: Line, *, start: float, rounds: int = 4, names: str = "") -> list:
        """The step-by-step path between two curves from x = start: up (or down) to curve a, across to curve b,
        and again. With a = the new expenditure line and b = the 45° line these are the multiplier's rounds; with
        a = demand and b = supply it is the cobweb. Sets the lettered path (names: one letter per corner on curve a,
        e.g. "abcd") and returns its points; reveal it round by round with params(path_upto=...)."""
        if rounds < 1:
            raise ValueError("a staircase has at least one round")
        x = float(start)
        pts = [(x, float(b.f(x)), "")]
        for r in range(rounds):
            y = float(a.f(x))
            pts.append((x, y, names[r] if r < len(names) else ""))
            try:
                x = self.at_price(b, y)
            except ValueError:
                break                                   # the path has left the frame
            pts.append((x, y, ""))
        self.path = [(round(px, 4), round(py, 4), n) for px, py, n in pts]
        return self.path

    # ------------------------------------------------------------------ the firm: marginal and average from a total
    def marginal(self, name: str, total, **kw) -> Line:
        """The marginal curve of a total function (MC from TC, MR from TR, MP from TP): its slope at each quantity."""
        e = 1e-4 * max(1.0, abs(self.xmax - self.xmin))
        return self.curve(name, lambda q, t=total, e=e: (t(q + e) - t(q - e)) / (2 * e), **kw)

    def average(self, name: str, total, **kw) -> Line:
        """The average curve of a total function (AC from TC, AP from TP): total ÷ quantity."""
        return self.curve(name, lambda q, t=total: t(q) / q, **kw)

    def revenue_marginal(self, name: str, demand: Line, **kw) -> Line:
        """Marginal revenue of a demand (average revenue) curve: the slope of P × Q. For a straight demand line it
        falls twice as fast and meets the quantity axis halfway."""
        return self.marginal(name, lambda q, f=demand.f: f(q) * q, **kw)

    # ------------------------------------------------------------------ scarcity and distribution
    def ppf(self, name: str, *, x_max: float, y_max: float, bow: float = 2.0, **kw) -> Line:
        """A production possibility curve from (0, y_max) to (x_max, 0). bow > 1 bows it outward (the opportunity
        cost rises as more of X is made); bow = 1 is a straight line (a constant opportunity cost)."""
        if bow < 1:
            raise ValueError("a production possibility curve is straight (bow 1) or bowed outward (bow > 1)")
        f = lambda x, a=x_max, b=y_max, k=bow: b * max(0.0, 1 - (x / a) ** k) ** (1 / k)  # noqa: E731
        n = max(2, self.samples)
        xs = tuple(x_max * math.sin(math.pi / 2 * i / n) ** (2 / bow) for i in range(n + 1))
        line = self.curve(name, f, domain=(0.0, x_max), xs=xs, **kw)
        line.meta = {"x_max": x_max, "y_max": y_max, "bow": bow}
        return line

    def piecewise(self, name: str, points: list, **kw) -> Line:
        """A line through the given (x, y) points, straight between them (a kinked demand curve, a tax schedule)."""
        pts = sorted((float(x), float(y)) for x, y in points)
        if len(pts) < 2 or len({x for x, _ in pts}) != len(pts):
            raise ValueError("a piecewise line needs two or more points with different x")

        def f(q, pts=pts):
            if q <= pts[0][0]:
                (x1, y1), (x2, y2) = pts[0], pts[1]
            elif q >= pts[-1][0]:
                (x1, y1), (x2, y2) = pts[-2], pts[-1]
            else:
                k = next(i for i in range(1, len(pts)) if q <= pts[i][0])
                (x1, y1), (x2, y2) = pts[k - 1], pts[k]
            return y1 + (y2 - y1) * (q - x1) / (x2 - x1)

        return self.curve(name, f, domain=(pts[0][0], pts[-1][0]), xs=tuple(x for x, _ in pts), **kw)

    def lorenz(self, name: str, shares: list, **kw) -> Line:
        """The Lorenz curve from the income shares of equal-sized groups, poorest first (five quintile shares that add
        up to 100): cumulative % of people against cumulative % of income. line.meta["gini"] is the Gini coefficient
        of these groups; the line of complete equality is linear(intercept=0, slope=1)."""
        total = float(sum(shares))
        if total <= 0 or any(s < 0 for s in shares) or list(shares) != sorted(shares):
            raise ValueError("Lorenz shares are non-negative and listed poorest group first")
        n, cum, pts = len(shares), 0.0, [(0.0, 0.0)]
        for i, s in enumerate(shares, 1):
            cum += s
            pts.append((100.0 * i / n, 100.0 * cum / total))
        line = self.piecewise(name, pts, **kw)
        area = sum((x2 - x1) * (y1 + y2) / 2 for (x1, y1), (x2, y2) in zip(pts, pts[1:]))
        line.meta = {"gini": round(1 - area / 5000.0, 4)}
        return line

    # ------------------------------------------------------------------ out: the saancha's parameters
    def _pts(self, line: Line) -> str:
        if "vertical" in line.meta:
            x, lo, hi = line.meta["vertical"]
            return f"{_fmt(x)},{_fmt(lo)} {_fmt(x)},{_fmt(hi)}"
        x0, x1 = line.domain or (self.xmin, self.xmax)
        n = max(2, self.samples)
        rows = []
        for q in (line.xs or [x0 + (x1 - x0) * i / n for i in range(n + 1)]):
            try:
                p = float(line.f(q))
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            if not math.isfinite(p) or p < self.ymin - 1e-9 or p > self.ymax + 1e-9:
                continue
            rows.append(f"{_fmt(q)},{_fmt(p)}")
        return " ".join(rows)

    def params(self, *, show: list | None = None, grow: list | None = None, bold: list | None = None, areas: list | None = None,
               dots: list | None = None, draw_in: float = 0.0, extras=True, slide: dict | None = None,
               morph_from: dict | None = None, along: list | None = None, path_upto: int | None = None,
               glide: float | None = None) -> dict:
        """The graph saancha's parameters for one state. show: the lines visible (all by default); grow: the lines (and
        area numbers as "a<n>") that draw over draw_in seconds after the step that sets this state; areas: which area
        numbers are visible (all by default); dots: which points are visible (all by default); extras: True for every
        mark, False for none, or the kinds to show ("hlines", "vlines", "arrows", "gaps", "xTicks", "yTicks", "segs",
        "path"); slide {line: (dx, dy)}: the line slides in from that offset after the step; morph_from {line: old_line}:
        the line reshapes from the old line's points; along [(line, f, label), (line, f, label, f0)]: a point on the
        curve at fraction f of its points, gliding from f0 ({x} {y} in the label read its values); path_upto: how many
        points of the lettered path are shown; glide: seconds those moves take."""
        p = {"w": self.w, "xmin": self.xmin, "xmax": self.xmax, "ymin": self.ymin, "ymax": self.ymax,
             "lines": ";".join(f"{l.name}:{self._pts(l)}" for l in self.lines)}
        if self.x_label:
            p["xLabel"] = self.x_label
        if self.y_label:
            p["yLabel"] = self.y_label
        if self.title:
            p["title"] = self.title
        if not self.smooth:
            p["smooth"] = False
        dashed = [str(l.index) for l in self.lines if l.dashed]
        if dashed:
            p["dashed"] = ",".join(dashed)
        colors = [f"{l.index}:{l.color}" for l in self.lines if l.color]
        if colors:
            p["colors"] = ";".join(colors)
        p["show"] = ",".join(str(l.index) for l in (show if show is not None else self.lines))
        p["grow"] = ",".join(str(g) if isinstance(g, str) else str(g.index) for g in (grow or []))
        if bold:
            p["bold"] = ",".join(str(l.index) for l in bold)
        if draw_in:
            p["drawIn"] = draw_in
        keep = set(areas) if areas is not None else set(range(1, len(self.areas) + 1))
        if self.areas:
            p["areas"] = ";".join(
                f"{label}:{' '.join(f'{_fmt(x)},{_fmt(y)}' for x, y in pts)}" + (f"@{color}" if color else "")
                for k, (pts, label, color) in enumerate(self.areas, 1) if k in keep) if keep else ""
        shown_dots = dots if dots is not None else self.dots
        if shown_dots:
            p["dots"] = ";".join(
                f"{_fmt(d.x)},{_fmt(d.y)}" + (f"<{_fmt(d.glide_from.x)},{_fmt(d.glide_from.y)}" if getattr(d, "glide_from", None) else "")
                + (f":{d.name}" if d.name else "") for d in shown_dots)
        if slide:
            p["slide"] = ";".join(f"{l.index}:{_fmt(d[0])},{_fmt(d[1])}" for l, d in slide.items())
        if morph_from:
            p["morph"] = ";".join(f"{l.index}:{self._pts(old)}" for l, old in morph_from.items())
        if along:
            p["along"] = ";".join(f"{a[0].index}@{_fmt(a[1])}" + (f"<{a[0].index}@{_fmt(a[3])}" if len(a) > 3 else "")
                                  + (f":{a[2]}" if len(a) > 2 and a[2] else "") for a in along)
        if glide:
            p["glide"] = glide
        kinds = {"hlines", "vlines", "arrows", "gaps", "xTicks", "yTicks", "segs", "path"} if extras is True else set(extras or ())
        if kinds:
            if self.hlines and "hlines" in kinds:
                p["hlines"] = ";".join(f"{_fmt(y)}:{lab}" for y, lab in self.hlines)
            if self.vlines and "vlines" in kinds:
                p["vlines"] = ";".join(f"{_fmt(x)}:{lab}" for x, lab in self.vlines)
            if self.arrows and "arrows" in kinds:
                p["arrows"] = ";".join(f"{_fmt(a[0])},{_fmt(a[1])}>{_fmt(b[0])},{_fmt(b[1])}" + (f":{lab}" if lab else "")
                                       for a, b, lab in self.arrows)
            if self.gaps and "gaps" in kinds:
                p["gaps"] = ";".join(f"{_fmt(x1)},{_fmt(x2)}@{_fmt(y)}" + (f":{lab}" if lab else "") for x1, x2, y, lab in self.gaps)
            if self.xticks and "xTicks" in kinds:
                p["xTicks"] = ";".join(f"{_fmt(x)}:{lab}" for x, lab in self.xticks)
            if self.yticks and "yTicks" in kinds:
                p["yTicks"] = ";".join(f"{_fmt(y)}:{lab}" for y, lab in self.yticks)
            if self.segs and "segs" in kinds:
                p["segs"] = ";".join(f"{_fmt(a[0])},{_fmt(a[1])}>{_fmt(b[0])},{_fmt(b[1])}" + (f":{lab}" if lab else "")
                                     for a, b, lab in self.segs)
            if self.path and "path" in kinds:
                p["path"] = ";".join(f"{_fmt(x)},{_fmt(y)}" + (f":{n}" if n else "") for x, y, n in self.path)
                if path_upto is not None:
                    p["pathUpto"] = path_upto
        return p

    def item(self, **state) -> dict:
        """An item thing for the plan: {"draw": "graph", "p": params}."""
        return {"draw": "graph", "p": self.params(**state)}
