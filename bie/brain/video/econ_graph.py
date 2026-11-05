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
    p = g.params(show=[D, S])                            # the first state; g.step(...) gives later states
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class Line:
    name: str
    f: object                       # P = f(Q): a callable over the x range
    color: str = ""
    dashed: bool = False
    domain: tuple = ()               # (x0, x1) to draw over; the whole range by default
    index: int = 0                   # 1-based place in the saancha's lines


@dataclass
class Point:
    x: float
    y: float
    name: str = ""


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
    lines: list = field(default_factory=list)
    areas: list = field(default_factory=list)
    dots: list = field(default_factory=list)
    hlines: list = field(default_factory=list)
    vlines: list = field(default_factory=list)
    arrows: list = field(default_factory=list)
    gaps: list = field(default_factory=list)
    xticks: list = field(default_factory=list)
    yticks: list = field(default_factory=list)

    # ------------------------------------------------------------------ curves
    def curve(self, name: str, f, *, color: str = "", dashed: bool = False, domain: tuple = ()) -> Line:
        """Any P = f(Q) (a cost curve, an indifference curve solved for y, a Lorenz curve): sampled smoothly."""
        if len(self.lines) >= 6:
            raise ValueError("the graph saancha draws at most six lines; split the idea over two graphs")
        line = Line(name, f, color, dashed, domain, len(self.lines) + 1)
        self.lines.append(line)
        return line

    def linear(self, name: str, *, intercept: float, slope: float, **kw) -> Line:
        """A straight line P = intercept + slope * Q (demand: slope < 0; supply: slope > 0)."""
        return self.curve(name, lambda q, a=intercept, b=slope: a + b * q, **kw)

    def through(self, name: str, p1: tuple, p2: tuple, **kw) -> Line:
        """A straight line through two (Q, P) points."""
        (x1, y1), (x2, y2) = p1, p2
        if x1 == x2:
            raise ValueError("a vertical line: use vline() (a fixed quantity)")
        slope = (y2 - y1) / (x2 - x1)
        return self.linear(name, intercept=y1 - slope * x1, slope=slope, **kw)

    def shift(self, line: Line, *, dx: float = 0.0, dy: float = 0.0, name: str = "", dashed: bool = True,
              color: str = "") -> Line:
        """The same curve moved: dx > 0 moves it right (more is bought or sold at every price), dy > 0 up (a tax on
        the sellers lifts supply by the tax)."""
        return self.curve(name or line.name + "2", lambda q, f=line.f: f(q - dx) + dy, dashed=dashed, color=color,
                          domain=tuple(v + dx for v in line.domain) if line.domain else ())

    # ------------------------------------------------------------------ what the economics computes
    def value(self, line: Line, q: float) -> float:
        return float(line.f(q))

    def cross(self, a: Line, b: Line, name: str = "", *, dot: bool = True) -> Point:
        """Where two curves meet (bisection on the difference over the x range): the equilibrium, MC = MR, AD = AS."""
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

    # ------------------------------------------------------------------ out: the saancha's parameters
    def _pts(self, line: Line) -> str:
        x0, x1 = line.domain or (self.xmin, self.xmax)
        n = max(2, self.samples)
        rows = []
        for i in range(n + 1):
            q = x0 + (x1 - x0) * i / n
            try:
                p = float(line.f(q))
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            if not math.isfinite(p) or p < self.ymin - 1e-9 or p > self.ymax + 1e-9:
                continue
            rows.append(f"{_fmt(q)},{_fmt(p)}")
        return " ".join(rows)

    def params(self, *, show: list | None = None, grow: list | None = None, bold: list | None = None, areas: list | None = None,
               dots: list | None = None, draw_in: float = 0.0, extras=True) -> dict:
        """The graph saancha's parameters for one state. show: the lines visible (all by default); grow: the lines (and
        area numbers as "a<n>") that draw over draw_in seconds after the step that sets this state; areas: which area
        numbers are visible (all by default); dots: which points are visible (all by default); extras: True for every
        mark, False for none, or the kinds to show ("hlines", "vlines", "arrows", "gaps", "xTicks", "yTicks")."""
        p = {"w": self.w, "xmin": self.xmin, "xmax": self.xmax, "ymin": self.ymin, "ymax": self.ymax,
             "lines": ";".join(f"{l.name}:{self._pts(l)}" for l in self.lines)}
        if self.x_label:
            p["xLabel"] = self.x_label
        if self.y_label:
            p["yLabel"] = self.y_label
        if self.title:
            p["title"] = self.title
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
        kinds = {"hlines", "vlines", "arrows", "gaps", "xTicks", "yTicks"} if extras is True else set(extras or ())
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
        return p

    def item(self, **state) -> dict:
        """An item thing for the plan: {"draw": "graph", "p": params}."""
        return {"draw": "graph", "p": self.params(**state)}
