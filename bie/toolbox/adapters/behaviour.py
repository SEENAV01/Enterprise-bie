"""Psychology, education and sociology computed in Python for BIE's blocks (Task 046a, batch 3).

- ``stroop``: a Stroop experiment's design by PsychoPy (``psychopy.data``): the routines of one trial and the
  randomised trial list (word × ink colour, congruent or not) that PsychoPy's TrialHandler gives for a seed, so the flow
  a learner sees is the one PsychoPy would run.
- ``teaching_method``: does a new teaching method raise grades? The logit model of Spector and Mazzeo (1980) on the
  data shipped with statsmodels (32 students; PSI = the new method), with the predicted chance of improving across
  grade point averages, with and without PSI, and the odds ratio for PSI with its 95 % interval.
"""
from __future__ import annotations

from .base import clean, need

STROOP_COLOURS = {"red": "#ff5a5a", "green": "#3ddc84", "blue": "#4f8dff", "yellow": "#ffd23f"}


def stroop(*, colours=("red", "green", "blue"), n_reps: int = 1, seed: int = 7) -> dict:
    data = need("psychopy")
    import psychopy
    conditions = [{"word": w.upper(), "ink": c, "congruent": w == c} for w in colours for c in colours]
    handler = data.TrialHandler(trialList=conditions, nReps=n_reps, method="random", seed=seed)
    trials = [{"n": handler.thisN, "word": t["word"], "ink": t["ink"], "ink_hex": STROOP_COLOURS.get(t["ink"], "#ffffff"),
               "congruent": bool(t["congruent"])} for t in handler]
    routines = [{"name": "fixation", "seconds": 0.5, "shows": "+"}, {"name": "stimulus", "seconds": None, "shows": "coloured word",
                 "ends": "key press: the ink colour"}, {"name": "feedback", "seconds": 0.3, "shows": "correct / wrong"}]
    return {"routines": routines, "trials": trials, "conditions": len(conditions), "repeats": n_reps, "seed": seed,
            "congruent": sum(t["congruent"] for t in trials), "incongruent": sum(not t["congruent"] for t in trials),
            "designed_by": f"PsychoPy {psychopy.__version__} (psychopy.data.TrialHandler)"}


def teaching_method(*, points: int = 41) -> dict:
    sm = need("statsmodels")
    np = need("numpy")
    import statsmodels.api as api
    frame = api.datasets.spector.load_pandas().data
    X = api.add_constant(frame[["GPA", "TUCE", "PSI"]], prepend=True)
    fit = api.Logit(frame["GRADE"], X).fit(disp=False)
    gpa = np.linspace(float(frame["GPA"].min()), float(frame["GPA"].max()), points)
    tuce = float(frame["TUCE"].mean())
    curves = {}
    for psi in (0, 1):
        grid = np.column_stack([np.ones(points), gpa, np.full(points, tuce), np.full(points, psi)])
        curves[psi] = fit.predict(grid)
    low, high = np.exp(fit.conf_int().loc["PSI"])
    return clean({"gpa": gpa, "with_psi": curves[1], "without_psi": curves[0], "tuce_mean": tuce, "n": int(fit.nobs),
                  "odds_ratio_psi": float(np.exp(fit.params["PSI"])), "odds_ratio_ci": [float(low), float(high)],
                  "p_value_psi": float(fit.pvalues["PSI"]), "pseudo_r2": float(fit.prsquared),
                  "data": "Spector and Mazzeo (1980), shipped with statsmodels (statsmodels.datasets.spector)",
                  "fitted_by": f"statsmodels {sm.__version__} Logit"}, 4)
