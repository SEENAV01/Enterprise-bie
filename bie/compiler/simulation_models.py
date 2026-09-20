"""H2-002 deterministic analytic models, with explicit units and view domains.

These are bounded mathematical models, not measured reality, a general solver,
or subject-expert/educational acceptance. No user-provided code is executed.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math
from .hardening_contracts import finite_number, known_properties, reject, text_value

MODELS = {
    "bie.sim.constant-acceleration-2d@1": {"state": {"x", "y", "vx", "vy"}, "params": {"ax", "ay"}, "units": {"x": "m", "y": "m", "vx": "m/s", "vy": "m/s", "ax": "m/s^2", "ay": "m/s^2", "t": "s"}, "axes": ["x (m)", "y (m)"], "assumptions": "Constant acceleration in a Cartesian plane; no collision or boundary dynamics."},
    "bie.sim.harmonic-oscillator-1d@1": {"state": {"x", "v"}, "params": {"omega"}, "units": {"x": "m", "v": "m/s", "omega": "rad/s", "t": "s"}, "axes": ["t (s)", "x (m)"], "assumptions": "Undamped linear oscillator x'' + omega^2 x = 0; no external forcing."},
    "bie.sim.exponential-decay@1": {"state": {"n"}, "params": {"rate"}, "units": {"n": "1", "rate": "1/s", "t": "s"}, "axes": ["t (s)", "n (dimensionless)"], "assumptions": "Continuous nonnegative state satisfying n' = -rate*n; not individual stochastic events."},
}

@dataclass(frozen=True)
class SimulationContract:
    model_ref: str
    initial_state: tuple[tuple[str, float], ...]
    parameters: tuple[tuple[str, float], ...]
    units: tuple[tuple[str, str], ...]
    start_ms: int
    duration_ms: int
    view: tuple[float, float, float, float]
    trajectory_samples: int
    title: str
    assumptions: str
    axes: tuple[str, str]
    execution_class: str = "analytic_model"
    solver: str = "closed-form.v1"
    accepted: bool = False

    def to_dict(self):
        out = asdict(self)
        for key in ("initial_state", "parameters", "units"):
            out[key] = dict(out[key])
        return out


def _numbers(value, keys, name):
    if not isinstance(value, dict) or set(value) != keys:
        reject("SIMULATION_SCHEMA_INVALID", name + " requires exactly: " + ", ".join(sorted(keys)))
    out = {k: finite_number(v, name + "." + k) for k, v in value.items()}
    if any(abs(v) > 1e8 for v in out.values()):
        reject("SIMULATION_NUMERIC_BOUNDS", name + " magnitude exceeds 1e8")
    return out


def evaluate_simulation(contract: SimulationContract, time_seconds: float) -> dict[str, float]:
    t = finite_number(time_seconds, "simulation time")
    if t < 0 or t > contract.duration_ms / 1000:
        reject("SIMULATION_TIME_OUT_OF_RANGE", "time must be within the model interval")
    s, p = dict(contract.initial_state), dict(contract.parameters)
    if contract.model_ref == "bie.sim.constant-acceleration-2d@1":
        state = {"x": s["x"] + s["vx"]*t + .5*p["ax"]*t*t,
                 "y": s["y"] + s["vy"]*t + .5*p["ay"]*t*t,
                 "vx": s["vx"] + p["ax"]*t, "vy": s["vy"] + p["ay"]*t}
        plot = (state["x"], state["y"])
    elif contract.model_ref == "bie.sim.harmonic-oscillator-1d@1":
        w = p["omega"]
        state = {"x": s["x"]*math.cos(w*t) + s["v"]/w*math.sin(w*t),
                 "v": -s["x"]*w*math.sin(w*t) + s["v"]*math.cos(w*t)}
        plot = (t, state["x"])
    elif contract.model_ref == "bie.sim.exponential-decay@1":
        state = {"n": s["n"]*math.exp(-p["rate"]*t)}
        plot = (t, state["n"])
    else:
        reject("SIMULATION_MODEL_UNSUPPORTED", "unknown model registry identity")
    result = {"t": t, **state, "plot_x": plot[0], "plot_y": plot[1]}
    if any(not math.isfinite(v) or abs(v) > 1e12 for v in result.values()):
        reject("SIMULATION_NUMERIC_BOUNDS", "model output exceeds finite supported bounds")
    return result


def _extents(c):
    s, p = dict(c.initial_state), dict(c.parameters)
    T = c.duration_ms / 1000
    if c.model_ref == "bie.sim.constant-acceleration-2d@1":
        points = [evaluate_simulation(c, 0), evaluate_simulation(c, T)]
        for pos, vel, acc in (("x", "vx", "ax"), ("y", "vy", "ay")):
            if p[acc] != 0 and 0 < -s[vel]/p[acc] < T:
                points.append(evaluate_simulation(c, -s[vel]/p[acc]))
        return min(v["x"] for v in points), max(v["x"] for v in points), min(v["y"] for v in points), max(v["y"] for v in points)
    if c.model_ref == "bie.sim.harmonic-oscillator-1d@1":
        amplitude = math.hypot(s["x"], s["v"]/p["omega"])
        return 0., T, -amplitude, amplitude
    return 0., T, s["n"]*math.exp(-p["rate"]*T), s["n"]


def simulation_contract(props: dict) -> SimulationContract:
    known_properties(props, {"model_ref", "execution_class", "initial_state", "parameters", "units", "start_ms", "duration_ms", "view", "trajectory_samples", "title", "receipt_ref"})
    ref = props.get("model_ref")
    if not isinstance(ref, str) or ref not in MODELS:
        reject("SIMULATION_MODEL_UNSUPPORTED", "a registered versioned analytic model_ref is required")
    if props.get("execution_class") == "verified_observed_execution" or "receipt_ref" in props:
        reject("SIMULATION_OBSERVATION_NOT_VERIFIED", "a reference string is not governed observed-execution evidence")
    if props.get("execution_class") != "analytic_model":
        reject("SIMULATION_EXECUTION_CLASS_REQUIRED", "this adapter explicitly executes an analytic_model")
    spec = MODELS[ref]
    s = _numbers(props.get("initial_state"), spec["state"], "initial_state")
    p = _numbers(props.get("parameters"), spec["params"], "parameters")
    if props.get("units") != spec["units"]:
        reject("SIMULATION_UNITS_MISMATCH", "supply the registry's explicit SI/dimensionless units")
    start, duration = props.get("start_ms", 0), props.get("duration_ms")
    if type(start) is not int or not 0 <= start <= 3600000 or type(duration) is not int or not 1 <= duration <= 600000:
        reject("SIMULATION_TIME_CONTRACT_INVALID", "integer start/duration in supported bounds required")
    if "omega" in p and not 1e-6 <= p["omega"] <= 100:
        reject("SIMULATION_PARAMETER_INVALID", "omega must be in 1e-6..100 rad/s")
    if "rate" in p and (p["rate"] < 0 or s["n"] < 0 or p["rate"]*duration/1000 > 500):
        reject("SIMULATION_PARAMETER_INVALID", "nonnegative n/rate and rate*duration <= 500 required")
    view = props.get("view")
    if not isinstance(view, dict) or set(view) != {"x_min", "x_max", "y_min", "y_max"}:
        reject("SIMULATION_VIEW_REQUIRED", "explicit x/y axis limits required")
    vals = tuple(finite_number(view[k], "view."+k) for k in ("x_min", "x_max", "y_min", "y_max"))
    if any(abs(v) > 1e12 for v in vals) or not (1e-9 <= vals[1]-vals[0] <= 1e12 and 1e-9 <= vals[3]-vals[2] <= 1e12):
        reject("SIMULATION_VIEW_INVALID", "finite nondegenerate view with supported numeric span required")
    required_samples = max(65, math.ceil(p.get("omega", 0)*duration/1000/(2*math.pi)*32) + 1)
    samples = props.get("trajectory_samples", required_samples)
    if type(samples) is not int or not required_samples <= samples <= 4097:
        reject("SIMULATION_SAMPLING_UNSUPPORTED", "trajectory needs sufficient temporal resolution within 4097 samples")
    c = SimulationContract(ref, tuple(sorted(s.items())), tuple(sorted(p.items())), tuple(sorted(spec["units"].items())), start, duration, vals, samples,
                           text_value(props.get("title", ref), "simulation title", maximum=160), spec["assumptions"], tuple(spec["axes"]))
    lo_x, hi_x, lo_y, hi_y = _extents(c)
    tol = 1e-10
    if lo_x < vals[0]-tol or hi_x > vals[1]+tol or lo_y < vals[2]-tol or hi_y > vals[3]+tol:
        reject("SIMULATION_VIEW_CLIPS_MODEL", "view must contain analytic interval/extrema; clipping is not silently accepted")
    for t in (0, duration/2000, duration/1000):
        evaluate_simulation(c, t)
    return c


def simulation_frame_state(c: SimulationContract, frame: int, fps: int):
    if type(frame) is not int or frame < 0 or type(fps) is not int or not 1 <= fps <= 240:
        reject("SIMULATION_FRAME_INVALID", "nonnegative integer frame and fps 1..240 required")
    return evaluate_simulation(c, min(c.duration_ms/1000, max(0, frame/fps-c.start_ms/1000)))


def simulation_js_evaluator(c: SimulationContract) -> str:
    expressions = {
      "bie.sim.constant-acceleration-2d@1": 'const x = s.x + s.vx*t + 0.5*p.ax*t*t; const y = s.y + s.vy*t + 0.5*p.ay*t*t; return {t, x, y, vx: s.vx+p.ax*t, vy: s.vy+p.ay*t, plot_x: x, plot_y: y};',
      "bie.sim.harmonic-oscillator-1d@1": 'const x = s.x*Math.cos(p.omega*t) + s.v/p.omega*Math.sin(p.omega*t); const v = -s.x*p.omega*Math.sin(p.omega*t) + s.v*Math.cos(p.omega*t); return {t, x, v, plot_x: t, plot_y: x};',
      "bie.sim.exponential-decay@1": 'const n = s.n*Math.exp(-p.rate*t); return {t, n, plot_x: t, plot_y: n};',
    }
    return expressions[c.model_ref]
