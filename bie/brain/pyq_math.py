"""Worked mathematics for the PYQ lab (Navin, 19 November 2026): exact values, units and the solving steps.

The maker writes a numerical question's working as short lines; this module evaluates every line exactly (fractions, not
floats, wherever the numbers allow), checks that every step's unit is what the line says, and keeps each intermediate
value so the player can show it and the narration can be checked against it. Nothing here knows a particular question.

    given u = 280 m/s "launch speed"
    given s = 0.5 "sin 30°"
    step uy = u * s : m/s "vertical part of the launch velocity"
    trap H_wrong = u^2 * s / (2*g) : m "only one sin θ"
    answer H

The projectile kit (``projectile``) writes these lines itself from the launch (speed, angle, g and what is asked), so a
projectile question gives only its numbers; the player draws the same model (``bie/brain/studio_pyq_player.html``).
"""
from __future__ import annotations

import ast
import math
import re
from fractions import Fraction

BASE = ("m", "s", "kg", "A", "K", "mol", "cd")
UNITS = {                       # unit symbol -> (factor, dimension exponents in BASE order)
    "m": (1, (1, 0, 0, 0, 0, 0, 0)), "cm": (Fraction(1, 100), (1, 0, 0, 0, 0, 0, 0)),
    "mm": (Fraction(1, 1000), (1, 0, 0, 0, 0, 0, 0)), "km": (1000, (1, 0, 0, 0, 0, 0, 0)),
    "s": (1, (0, 1, 0, 0, 0, 0, 0)), "min": (60, (0, 1, 0, 0, 0, 0, 0)), "h": (3600, (0, 1, 0, 0, 0, 0, 0)),
    "kg": (1, (0, 0, 1, 0, 0, 0, 0)), "g": (Fraction(1, 1000), (0, 0, 1, 0, 0, 0, 0)),
    "A": (1, (0, 0, 0, 1, 0, 0, 0)), "K": (1, (0, 0, 0, 0, 1, 0, 0)), "mol": (1, (0, 0, 0, 0, 0, 1, 0)),
    "N": (1, (1, -2, 1, 0, 0, 0, 0)), "J": (1, (2, -2, 1, 0, 0, 0, 0)), "W": (1, (2, -3, 1, 0, 0, 0, 0)),
    "Pa": (1, (-1, -2, 1, 0, 0, 0, 0)), "C": (1, (0, 1, 0, 1, 0, 0, 0)), "V": (1, (2, -3, 1, -1, 0, 0, 0)),
    "ohm": (1, (2, -3, 1, -2, 0, 0, 0)), "Hz": (1, (0, -1, 0, 0, 0, 0, 0)), "L": (Fraction(1, 1000), (3, 0, 0, 0, 0, 0, 0)),
}
NONE = (0, 0, 0, 0, 0, 0, 0)
DEG = {0: (Fraction(0), Fraction(1)), 30: (Fraction(1, 2), None), 60: (None, Fraction(1, 2)), 90: (Fraction(1), Fraction(0)),
       180: (Fraction(0), Fraction(-1))}
LINE = re.compile(r'^\s*(given|step|trap|answer)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=\s*(.*?))?\s*$')


class MathProblem(ValueError):
    pass


def parse_unit(text: str) -> tuple:
    """'m/s', 'm s^-2', 'm/s2', 'm^2/s^2' -> (factor, dims). Empty text: no unit."""
    text = (text or "").strip().replace("²", "^2").replace("³", "^3").replace("·", " ").replace("*", " ")
    if not text or text in ("-", "1"):
        return 1, NONE
    factor, dims = Fraction(1), [0] * 7
    sign = 1
    for token in re.findall(r"/|[A-Za-z]+(?:\^?-?[0-9]+)?", text):
        if token == "/":
            sign = -1
            continue
        match = re.fullmatch(r"([A-Za-z]+?)(?:\^?(-?[0-9]+))?", token)
        name, power = match.group(1), int(match.group(2) or 1)
        if name not in UNITS:
            raise MathProblem(f"unknown unit {name!r} in {text!r}")
        f, d = UNITS[name]
        factor *= Fraction(f) ** (sign * power)
        for i, e in enumerate(d):
            dims[i] += e * sign * power
    return factor, tuple(dims)


def unit_text(dims: tuple) -> str:
    up = [f"{b}^{e}" if e != 1 else b for b, e in zip(BASE, dims) if e > 0]
    down = [f"{b}^{-e}" if e != -1 else b for b, e in zip(BASE, dims) if e < 0]
    return (" ".join(up) or "1") + ("/" + " ".join(down) if down else "") if (up or down) else ""


class Q:
    """A value with dimensions; exact while it is a Fraction."""
    __slots__ = ("v", "d")

    def __init__(self, v, d=NONE):
        self.v, self.d = v, tuple(d)

    def _same(self, other, op):
        if self.d != other.d:
            raise MathProblem(f"cannot {op} {unit_text(self.d) or 'a number'} and {unit_text(other.d) or 'a number'}")

    def __add__(self, o):
        self._same(o, "add")
        return Q(self.v + o.v, self.d)

    def __sub__(self, o):
        self._same(o, "subtract")
        return Q(self.v - o.v, self.d)

    def __mul__(self, o):
        return Q(self.v * o.v, tuple(a + b for a, b in zip(self.d, o.d)))

    def __truediv__(self, o):
        if o.v == 0:
            raise MathProblem("division by zero")
        return Q(self.v / o.v, tuple(a - b for a, b in zip(self.d, o.d)))

    def __pow__(self, n: int):
        return Q(self.v ** n, tuple(a * n for a in self.d))

    def __neg__(self):
        return Q(-self.v, self.d)


def number(text) -> Fraction:
    text = str(text).replace(",", "").strip()
    try:
        return Fraction(text)
    except (ValueError, ZeroDivisionError):
        raise MathProblem(f"not a number: {text!r}")


def _sqrt(q: Q) -> Q:
    if any(e % 2 for e in q.d):
        raise MathProblem("square root of a unit with an odd power")
    v = q.v
    if isinstance(v, Fraction) and v >= 0:
        a, b = math.isqrt(v.numerator), math.isqrt(v.denominator)
        exact = Fraction(a, b) if a * a == v.numerator and b * b == v.denominator else None
    else:
        exact = None
    value = exact if exact is not None else Fraction(math.sqrt(float(v))).limit_denominator(10 ** 9)
    return Q(value, tuple(e // 2 for e in q.d))


def trig(name: str, q: Q) -> Q:
    """sin/cos/tan of an angle in degrees (exact at 0, 30, 60, 90; otherwise a close fraction)."""
    if q.d != NONE:
        raise MathProblem(f"{name} needs an angle in degrees")
    deg = q.v
    if deg in DEG and name in ("sin", "cos"):
        s, c = DEG[deg]
        exact = s if name == "sin" else c
        if exact is not None:
            return Q(exact)
    if name == "tan" and deg == 45:
        return Q(Fraction(1))
    f = {"sin": math.sin, "cos": math.cos, "tan": math.tan}[name](math.radians(float(deg)))
    return Q(Fraction(f).limit_denominator(10 ** 9))


def evaluate(expr: str, names: dict) -> Q:
    expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/").replace("−", "-")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        raise MathProblem(f"cannot read the expression {expr!r}")

    def walk(node):
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return Q(number(repr(node.value)) if isinstance(node.value, float) else Fraction(node.value))
        if isinstance(node, ast.Name):
            if node.id not in names:
                raise MathProblem(f"{node.id!r} is used before it is given or worked out")
            return names[node.id]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            value = walk(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Pow):
                power = walk(node.right)
                if power.d != NONE or power.v.denominator != 1:
                    raise MathProblem("powers must be whole numbers")
                return walk(node.left) ** int(power.v)
            left, right = walk(node.left), walk(node.right)
            ops = {ast.Add: Q.__add__, ast.Sub: Q.__sub__, ast.Mult: Q.__mul__, ast.Div: Q.__truediv__}
            if type(node.op) in ops:
                return ops[type(node.op)](left, right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args) == 1 and not node.keywords:
            arg = walk(node.args[0])
            if node.func.id == "sqrt":
                return _sqrt(arg)
            if node.func.id in ("sin", "cos", "tan"):
                return trig(node.func.id, arg)
        raise MathProblem(f"only + - * / ^, sqrt, sin, cos and tan are allowed (in {expr!r})")

    return walk(tree)


def fmt(v, places: int = 2) -> str:
    """19600 -> '19,600'; 0.5 -> '0.5'; 242.4871 -> '242.49'; exact fractions stay readable."""
    f = float(v)
    if abs(f - round(f)) < 1e-9:
        return f"{int(round(f)):,}"
    text = f"{f:,.{places}f}".rstrip("0").rstrip(".")
    return text


def is_exact(v) -> bool:
    return isinstance(v, Fraction) and v.denominator in (1, 2, 4, 5, 8, 10, 16, 20, 25, 40, 50, 100, 1000)


def work(lines: list) -> dict:
    """Evaluate the working lines. Returns {"values", "steps", "traps", "answer", "problems"}; never raises."""
    names, steps, traps, problems, answer = {}, [], [], [], None
    for raw in lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        body, label = raw, ""
        quoted = re.search(r'"([^"]*)"\s*$', raw)
        if quoted:
            label, body = quoted.group(1), raw[:quoted.start()]
        unit = ""
        if ":" in body:
            body, unit = body.rsplit(":", 1)
        match = LINE.match(body)
        if not match:
            problems.append(f"working line not understood: {raw!r} (use given/step/trap/answer)")
            continue
        kind, name, rhs = match.groups()
        try:
            if kind == "answer":
                if name not in names:
                    raise MathProblem(f"answer {name!r} is never worked out")
                answer = name
                continue
            if rhs is None:
                raise MathProblem("a value is missing after '='")
            if kind == "given":
                parts = rhs.split(None, 1)
                factor, dims = parse_unit(parts[1] if len(parts) > 1 else unit)
                value = Q(number(parts[0]) * factor, dims)
                names[name] = value
                steps.append({"name": name, "kind": "given", "expr": rhs.strip(), "value": value.v, "dims": dims,
                              "unit": (parts[1] if len(parts) > 1 else unit).strip(), "label": label})
                continue
            value = evaluate(rhs, names)
            want = unit.strip()
            if want:
                factor, dims = parse_unit(want)
                if dims != value.d:
                    raise MathProblem(f"{name}: the working gives {unit_text(value.d) or 'no unit'}, the line says {want}")
                shown = value.v / factor
            else:
                shown = value.v
            row = {"name": name, "kind": kind, "expr": rhs.strip(), "value": shown, "dims": value.d,
                   "unit": want or unit_text(value.d), "label": label, "with_values": substitute(rhs, names)}
            (traps if kind == "trap" else steps).append(row)
            if kind == "step":
                names[name] = value
            else:
                names[name] = value          # a trap's value can be compared too, but it never feeds the answer
        except MathProblem as exc:
            problems.append(f"working line {raw.strip()!r}: {exc}")
    if answer is None and not problems:
        problems.append("the working has no 'answer <name>' line")
    return {"values": {k: v.v for k, v in names.items()}, "dims": {k: v.d for k, v in names.items()}, "steps": steps,
            "traps": traps, "answer": answer, "problems": problems}


def substitute(expr: str, names: dict) -> str:
    """'u * s' -> '280 × 0.5' with the known values (for the solving board)."""
    def rep(match):
        name = match.group(0)
        if name in ("sqrt", "sin", "cos", "tan") or name not in names:
            return name
        return fmt(names[name].v)
    text = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", rep, expr)
    return text.replace("**", "^").replace("*", " × ").replace("/", " ÷ ").replace("  ", " ")


def clear_decimal(num, den) -> dict | None:
    """19600 ÷ 19.6 -> multiply both by 10 -> 196000 ÷ 196 (why: the divisor becomes a whole number)."""
    num, den = Fraction(num), Fraction(den)
    if den.denominator == 1 and num.denominator == 1:
        return None
    for k in range(1, 7):
        scale = 10 ** k
        if (den * scale).denominator == 1 and (num * scale).denominator == 1:
            return {"times": scale, "num": num * scale, "den": den * scale, "value": num / den}
    return None


def option_numbers(text: str) -> list:
    """Numbers written in an option ('1000 m', '2,800 m', '1/4') as Fractions."""
    out = []
    for raw in re.findall(r"-?\d[\d,]*(?:\.\d+)?(?:/\d+)?", text or ""):
        try:
            out.append(Fraction(raw.replace(",", "")))
        except (ValueError, ZeroDivisionError):
            pass
    return out


def close(a, b, rel: float = 0.006) -> bool:
    a, b = float(a), float(b)
    return abs(a - b) <= rel * max(abs(a), abs(b), 1e-12)


def match_option(value, options: list, rel: float = 0.006) -> int | None:
    """The index of the one option whose first number is this value (within 0.6 %, the rounding exams use)."""
    hits = [i for i, text in enumerate(options) if option_numbers(text) and close(option_numbers(text)[0], value, rel)]
    return hits[0] if len(hits) == 1 else None


# --- the projectile kit -------------------------------------------------------------------------------------------------
ASKED = ("max_height", "time_to_peak", "flight_time", "range")
PROJECTILE_KEYS = re.compile(r"^\s*(u|theta|g|sin|cos|asked|ref)\s*=\s*(.+?)\s*$")


def projectile_params(lines: list) -> tuple:
    params, problems = {"g": "9.8 m/s2"}, []
    for raw in lines:
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        match = PROJECTILE_KEYS.match(raw)
        if not match:
            problems.append(f"projectile line not understood: {raw!r} (u, theta, g, sin, cos, asked, ref)")
            continue
        params[match.group(1)] = match.group(2)
    for key in ("u", "theta", "asked"):
        if key not in params:
            problems.append(f"projectile: '{key} = ...' is missing")
    if params.get("asked") and params["asked"] not in ASKED:
        problems.append(f"projectile: asked must be one of {', '.join(ASKED)}")
    return params, problems


def projectile(lines: list) -> dict:
    """The ideal projectile (no air drag, uniform g, landing at the launch level) and its standard working."""
    params, problems = projectile_params(lines)
    if problems:
        return {"problems": problems}
    u_val, u_unit = (params["u"].split(None, 1) + ["m/s"])[:2]
    theta = params["theta"].split()[0]
    g_val, g_unit = (params["g"].split(None, 1) + ["m/s2"])[:2]
    sin_line = f'given s = {params["sin"]} "sin θ, as the question gives it"' if "sin" in params else \
        f'step s = sin(theta) "sin θ"'
    cos_line = f'given c = {params["cos"]} "cos θ, as the question gives it"' if "cos" in params else \
        f'step c = cos(theta) "cos θ"'
    asked = params["asked"]
    working = [f'given u = {u_val} {u_unit} "launch speed (the whole, slanted velocity)"',
               f'given theta = {theta} "launch angle above the horizontal"',
               f'given g = {g_val} {g_unit} "gravity, pulling down"', sin_line, cos_line,
               'step uy = u * s : m/s "vertical part: the side opposite θ"',
               'step ux = u * c : m/s "horizontal part: the side next to θ"']
    if asked == "max_height":
        working += ['step uy2 = uy^2 : m^2/s^2 "the whole vertical part, squared"',
                    'step two_g = 2 * g : m/s^2 "2g"',
                    'step H = uy2 / two_g : m "0 = uᵧ² − 2gH, so H = uᵧ²/2g"',
                    'trap H_one_sin = u^2 * s / two_g : m "only one sin θ: u² sin θ / 2g"',
                    'trap H_whole_u = u^2 / two_g : m "the whole speed used as if it went straight up"', "answer H"]
    elif asked == "time_to_peak":
        working += ['step t_up = uy / g : s "vᵧ = uᵧ − g t = 0 at the top"',
                    'trap t_whole_u = u / g : s "the whole speed used as if it went straight up"', "answer t_up"]
    elif asked == "flight_time":
        working += ['step t_up = uy / g : s "time to the top"', 'step T = 2 * t_up : s "up and down take the same time"',
                    'trap T_half = t_up : s "only the way up"', "answer T"]
    else:
        working += ['step t_up = uy / g : s "time to the top"', 'step T = 2 * t_up : s "whole flight time"',
                    'step R = ux * T : m "horizontal speed stays the same for the whole flight"',
                    'trap R_up_only = ux * t_up : m "only the way up"', "answer R"]
    result = work(working)
    values = result["values"]
    if not result["problems"]:
        uy, ux, g = float(values["uy"]), float(values["ux"]), float(values["g"])
        result["flight"] = {"u": float(values["u"]), "theta": float(values["theta"]), "g": g, "ux": ux, "uy": uy,
                            "H": uy * uy / (2 * g), "T": 2 * uy / g, "R": ux * 2 * uy / g}
        if "ref" in params:
            m = re.match(r'\s*([0-9.,]+)\s*m\b\s*"?([^"]*)"?', params["ref"])
            if m:
                result["flight"]["ref"] = {"height": float(number(m.group(1))), "label": m.group(2).strip()}
        if asked == "max_height":
            split = clear_decimal(values["uy2"], values["two_g"])
            if split:
                result["clear_decimal"] = {k: fmt(v) for k, v in split.items()}
            result["square_split"] = square_split(values["uy"])
    result["asked"] = asked
    result["working"] = working
    return result


def square_split(x) -> dict | None:
    """140² = 140 × (100 + 40) = 14,000 + 5,600 = 19,600: the square as two easy products."""
    x = Fraction(x)
    if x.denominator != 1 or x < 20:
        return None
    n = int(x)
    hundreds = (n // 100) * 100 if n >= 100 else (n // 10) * 10
    rest = n - hundreds
    if rest == 0:
        return {"x": fmt(n), "a": fmt(hundreds), "b": "0", "pa": fmt(n * hundreds), "pb": "0", "total": fmt(n * n)}
    return {"x": fmt(n), "a": fmt(hundreds), "b": fmt(rest), "pa": fmt(n * hundreds), "pb": fmt(n * rest), "total": fmt(n * n)}
