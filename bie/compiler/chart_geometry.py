"""H1-002: deterministic chart coordinates. No abs-value semantic fallback."""
from __future__ import annotations
import math
from .hardening_contracts import known_properties, finite_number, label, reject, sequence, text_value

WIDTH, HEIGHT = 640, 400
LEFT, RIGHT, TOP, BOTTOM = 64.0, 604.0, 32.0, 316.0

def _domain(values):
    lo, hi = min(0.0, min(values)), max(0.0, max(values))
    return (-1.0, 1.0) if lo == hi else (lo, hi)

def chart_geometry(props: dict) -> dict:
    known_properties(props, {'units', 'categories', 'x_label', 'values', 'chart_kind', 'x_values', 'y_label'})
    kind = props.get("chart_kind")
    if kind not in {"bar", "line", "area", "scatter", "pie"}:
        reject("CHART_KIND_UNSUPPORTED", "no implicit chart fallback is permitted")
    categories = sequence(props.get("categories"), "categories")
    categories = [text_value(x, "category", maximum=256) for x in categories]
    values = [finite_number(v, "value") for v in sequence(props.get("values"), "values")]
    if len(values) != len(categories):
        reject("CHART_DATA_LENGTH_MISMATCH", "categories and values must have equal length")
    if kind != "scatter" and "x_values" in props:
        reject("CHART_UNUSED_X_VALUES", "numeric x_values are only consumed by scatter")
    data = {"kind": kind, "categories": categories, "values": values,
            "units": label(props, "units"), "x_label": label(props, "x_label"),
            "y_label": label(props, "y_label"), "width": WIDTH, "height": HEIGHT,
            "left": LEFT, "right": RIGHT, "top": TOP, "bottom": BOTTOM,
            "bars": [], "points": [], "slices": [], "line_points": "", "area_points": ""}
    if kind == "pie":
        if any(v < 0 for v in values):
            reject("PIE_NEGATIVE_VALUE_UNSUPPORTED", "signed quantities must not be represented as pie slices")
        total = math.fsum(values)
        if total <= 0:
            reject("PIE_ZERO_TOTAL", "pie requires a positive total")
        start, positive = -math.pi / 2, sum(v > 0 for v in values)
        for i, v in enumerate(values):
            if v == 0:
                continue
            sweep = 2 * math.pi * (v / total)
            end = start + sweep
            if positive == 1:
                path = "M 320 30 A 140 140 0 1 1 320 310 A 140 140 0 1 1 320 30 Z"
            else:
                x1, y1 = 320 + 140 * math.cos(start), 170 + 140 * math.sin(start)
                x2, y2 = 320 + 140 * math.cos(end), 170 + 140 * math.sin(end)
                path = f"M 320 170 L {x1:.12g} {y1:.12g} A 140 140 0 {int(sweep > math.pi)} 1 {x2:.12g} {y2:.12g} Z"
            data["slices"].append({"index": i, "label": categories[i], "value": v,
                "fraction": v / total, "path": path})
            start = end
        data.update({"domain": None, "baseline": None})
        return data
    lo, hi = _domain(values)
    def y(value):
        return BOTTOM - (value - lo) / (hi - lo) * (BOTTOM - TOP)
    baseline = y(0.0)
    data.update({"domain": [lo, hi], "baseline": baseline})
    if kind == "scatter":
        xs = [finite_number(x, "x value") for x in sequence(props.get("x_values"), "x_values")]
        if len(xs) != len(values):
            reject("CHART_DATA_LENGTH_MISMATCH", "scatter x_values and values must have equal length")
        xlo, xhi = _domain(xs)
        positions = [LEFT + (x - xlo) / (xhi - xlo) * (RIGHT - LEFT) for x in xs]
        data.update({"x_values": xs, "x_domain": [xlo, xhi]})
    elif kind == "bar":
        step = (RIGHT - LEFT) / len(values)
        positions = [LEFT + step * (i + 0.5) for i in range(len(values))]
    else:
        positions = [(LEFT + RIGHT) / 2] if len(values) == 1 else [LEFT + (RIGHT - LEFT) * i / (len(values) - 1) for i in range(len(values))]
    for i, (x, value) in enumerate(zip(positions, values)):
        py = y(value)
        data["points"].append({"index": i, "label": categories[i], "value": value, "x": x, "y": py})
        if kind == "bar":
            width = (RIGHT - LEFT) / len(values) * 0.72
            data["bars"].append({"index": i, "label": categories[i], "value": value,
                "x": x - width / 2, "y": min(py, baseline), "width": width,
                "height": abs(py - baseline)})
    if kind in {"line", "area"}:
        data["line_points"] = " ".join(f"{p['x']:.12g},{p['y']:.12g}" for p in data["points"])
        if kind == "area":
            data["area_points"] = f"{positions[0]:.12g},{baseline:.12g} " + data["line_points"] + f" {positions[-1]:.12g},{baseline:.12g}"
    return data
