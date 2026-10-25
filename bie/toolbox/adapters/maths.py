"""Maths computed and checked in Python (SymPy, statsmodels) for BIE's web blocks (Task 046a).

- ``equation_steps``: the steps of solving an equation; SymPy proves that every step has exactly the solutions of
  the step before it (so BIE never shows a wrong step) and writes each step in LaTeX for KaTeX.
- ``function_samples``: points of y = f(x) for a graph drawn over time, with its LaTeX.
- ``regression``: an ordinary least squares line through data (statsmodels), with slope, intercept and R squared.
"""
from __future__ import annotations

from .base import clean, need


class StepError(ValueError):
    """A step does not follow from the one before it."""


def _parse(text: str, symbols: dict, *, evaluate: bool = True):
    """``evaluate=False`` keeps the step as the learner reads it (3(x - 2) + 4 stays, not 3x - 2) for the LaTeX."""
    sympy = need("sympy")
    from sympy.parsing.sympy_parser import (convert_xor, implicit_multiplication_application, parse_expr,
                                            standard_transformations)
    transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
    if text.count("=") != 1:
        raise StepError(f"{text!r}: a step needs exactly one '='")
    left, right = text.split("=")
    return sympy.Eq(parse_expr(left, local_dict=symbols, transformations=transformations, evaluate=evaluate),
                    parse_expr(right, local_dict=symbols, transformations=transformations, evaluate=evaluate), evaluate=False)


def equation_steps(steps: list, variable: str = "x", *, domain: str = "real") -> dict:
    """Each step as LaTeX with ``checked`` = SymPy found the same solution set as the step before.

    Raises ``StepError`` for an unreadable step; a step that changes the solutions is returned with checked False and
    the reason, and ``all_checked`` is False (a demo or a scene must refuse to show it)."""
    sympy = need("sympy")
    x = sympy.Symbol(variable, real=(domain == "real"))
    symbols = {variable: x}
    space = sympy.S.Reals if domain == "real" else sympy.S.Complexes
    out, previous = [], None
    for text in steps:
        eq = _parse(text, symbols)
        solutions = sympy.solveset(eq.lhs - eq.rhs, x, domain=space)
        written = _parse(text, symbols, evaluate=False)
        latex = sympy.latex(written.lhs, order="none") + " = " + sympy.latex(written.rhs, order="none")
        row = {"text": text, "latex": latex, "solutions": sympy.latex(solutions)}
        if previous is None:
            row.update(checked=True, why="the starting equation")
        elif solutions == previous:
            row.update(checked=True, why=f"same solutions as the step before: {sympy.latex(solutions)}")
        else:
            row.update(checked=False, why=f"solutions changed from {sympy.latex(previous)} to {sympy.latex(solutions)}")
        out.append(row)
        previous = solutions if previous is None or row["checked"] else previous
    return {"variable": variable, "steps": out, "all_checked": all(s["checked"] for s in out), "checked_by": "sympy.solveset"}


def function_samples(expression: str, *, x_min: float = -6.0, x_max: float = 6.0, points: int = 241, variable: str = "x") -> dict:
    sympy = need("sympy")
    np = need("numpy")
    x = sympy.Symbol(variable, real=True)
    from sympy.parsing.sympy_parser import (convert_xor, implicit_multiplication_application, parse_expr,
                                            standard_transformations)
    expr = parse_expr(expression, local_dict={variable: x},
                      transformations=standard_transformations + (implicit_multiplication_application, convert_xor))
    f = sympy.lambdify(x, expr, "numpy")
    xs = np.linspace(x_min, x_max, points)
    with np.errstate(all="ignore"):
        ys = np.asarray(f(xs), dtype=float) * np.ones_like(xs)
    finite = ys[np.isfinite(ys)]
    return clean({"latex": "y = " + sympy.latex(expr), "x": xs, "y": ys, "y_min": float(finite.min()) if finite.size else None,
                  "y_max": float(finite.max()) if finite.size else None, "derivative_latex": sympy.latex(sympy.diff(expr, x)),
                  "computed_by": "sympy.lambdify + numpy"})


def regression(x: list, y: list) -> dict:
    sm = need("statsmodels")
    np = need("numpy")
    import statsmodels.api as api
    xs, ys = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    model = api.OLS(ys, api.add_constant(xs)).fit()
    intercept, slope = (float(v) for v in model.params)
    line_x = [float(xs.min()), float(xs.max())]
    return clean({"x": xs, "y": ys, "slope": slope, "intercept": intercept, "r_squared": float(model.rsquared),
                  "p_value_slope": float(model.pvalues[1]), "line": {"x": line_x, "y": [intercept + slope * v for v in line_x]},
                  "computed_by": f"statsmodels {sm.__version__} OLS"})
