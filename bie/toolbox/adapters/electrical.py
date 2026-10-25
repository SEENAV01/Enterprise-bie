"""Electrical and electronics computed in Python for BIE's web blocks to draw (Task 046a, batch 2).

- ``circuit_parts``: a circuit drawn by schemdraw, returned as one SVG viewBox and one SVG piece per element, in the
  order they were placed, so a block can build the circuit part by part.
- ``rc_charge``: a capacitor charging through a resistor, simulated by ngspice (a transient analysis) and solved by
  lcapy (the exact formula); the two must agree before the numbers are shown.
- ``step_responses``: the step response of a second-order system for several damping ratios, by python-control,
  cross-checked with SciPy's signal module.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from .base import clean, need, need_program

_TAG = re.compile(r"<(?:path|circle|text|polygon|polyline|ellipse|line|rect)\b[^>]*?(?:/>|>.*?</(?:text|path)>)", re.S)


def circuit_parts(parts: list, *, colour: str = "#f2f6f8", fontsize: int = 15) -> dict:
    """``parts`` = [(element name, direction, label, extra keyword arguments)], e.g. ("Resistor", "right", "1 kΩ", {}).
    Directions: up, down, left, right; "tox:0" on a Line closes the loop back to x = 0."""
    schemdraw = need("schemdraw")
    import schemdraw.elements as elm
    schemdraw.use("svg")

    def drawing(count: int):
        d = schemdraw.Drawing(show=False)
        d.config(fontsize=fontsize, color=colour, lw=2.4)
        for name, direction, label, extra in parts[:count]:
            element = getattr(elm, name)(**(extra or {}))
            if direction.startswith("tox:"):
                element = element.left().tox(float(direction.split(":")[1]))
            else:
                element = getattr(element, direction)()
            if label:
                element = element.label(label)
            d += element
        return d.get_imagedata("svg").decode()

    from collections import Counter
    full = drawing(len(parts))
    view = re.search(r'viewBox="([^"]+)"', full).group(1)
    # schemdraw groups its output by kind (paths, then text), so each element's piece is what drawing one more element
    # adds; coordinates are absolute, so the earlier pieces are the same strings in every later drawing.
    pieces, before = [], Counter()
    for count in range(1, len(parts) + 1):
        tags = _TAG.findall(drawing(count))
        now = Counter(tags)
        if before - now:
            raise ValueError("an earlier circuit element changed when the next one was added")
        new, extra = [], now - before
        for tag in tags:
            if extra[tag]:
                new.append(tag)
                extra[tag] -= 1
        pieces.append("".join(new))
        before = now
    return {"view_box": view, "pieces": pieces, "labels": [p[2] for p in parts], "drawn_by": f"schemdraw {schemdraw.__version__}"}


def rc_charge(resistance: float = 1000.0, capacitance: float = 100e-6, voltage: float = 5.0, *, t_end: float | None = None,
              points: int = 121) -> dict:
    """V(capacitor) after a switch closes: ngspice's transient analysis and lcapy's formula, compared point by point."""
    np = need("numpy")
    lcapy = need("lcapy")
    program = need_program("ngspice")
    tau = resistance * capacitance
    t_end = t_end or 5 * tau
    step = t_end / (points - 1)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "vc.txt"
        netlist = Path(tmp) / "rc.cir"
        netlist.write_text("\n".join([
            "* BIE toolbox: RC charging",
            f"V1 in 0 PWL(0 0 1n {voltage})",
            f"R1 in out {resistance}",
            f"C1 out 0 {capacitance} IC=0",
            ".control",
            f"tran {step} {t_end} 0 {step / 10} uic",
            f"linearize v(out)",
            f"wrdata {out} v(out)",
            ".endc",
            ".end", ""]), encoding="utf-8")
        done = subprocess.run([program, "-b", str(netlist)], capture_output=True, text=True, timeout=120)
        if done.returncode != 0 or not out.exists():
            raise RuntimeError(f"ngspice failed: {(done.stderr or done.stdout)[-800:]}")
        raw = np.loadtxt(out)
    times = np.linspace(0.0, t_end, points)
    simulated = np.interp(times, raw[:, 0], raw[:, 1])
    circuit = lcapy.Circuit(f"""
V1 1 0 step {voltage}
R1 1 2 {resistance}
C1 2 0 {capacitance}""")
    formula = circuit.C1.V(lcapy.t)
    exact = np.array([float(formula.evaluate(float(t))) if t > 0 else 0.0 for t in times])
    error = float(np.max(np.abs(simulated - exact)))
    return clean({"t": times, "v_spice": simulated, "v_exact": exact, "tau": tau, "voltage": voltage,
                  "formula_latex": formula.latex(), "max_difference": error, "agree": error < 0.02 * voltage,
                  "simulated_by": "ngspice (transient)", "solved_by": f"lcapy {lcapy.__version__}"})


def step_responses(zetas=(0.2, 0.5, 1.0), *, wn: float = 2.0, t_end: float = 8.0, points: int = 241) -> dict:
    """Step responses of wn² / (s² + 2ζwn s + wn²); python-control computes, SciPy's signal module checks."""
    np = need("numpy")
    control = need("python-control")
    signal = need("scipy-signal")
    times = np.linspace(0.0, t_end, points)
    rows = []
    for zeta in zetas:
        num, den = [wn ** 2], [1.0, 2 * zeta * wn, wn ** 2]
        _, y = control.step_response(control.tf(num, den), times)
        _, y_check = signal.step((num, den), T=times)
        info = control.step_info(control.tf(num, den))
        rows.append({"zeta": zeta, "y": np.asarray(y), "overshoot_percent": info["Overshoot"],
                     "settling_time": info["SettlingTime"], "checked": bool(np.max(np.abs(np.asarray(y) - y_check)) < 1e-3)})
    return clean({"t": times, "wn": wn, "responses": rows, "all_checked": all(r["checked"] for r in rows),
                  "computed_by": f"python-control {control.__version__}", "checked_by": "scipy.signal.step"})
