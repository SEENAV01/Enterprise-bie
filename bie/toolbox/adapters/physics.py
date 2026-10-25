"""Physics computed in Python (NumPy, SciPy) for BIE's web blocks to draw (Task 046a).

- ``falling_body``: a body dropped from a height, with air drag (SciPy ODE) and without (NumPy formula), sampled at
  every video frame, plus the moment it lands.
- ``wave``: two travelling waves and their sum (a standing wave), sampled per frame (NumPy).
"""
from __future__ import annotations

from .base import clean, need


def falling_body(height: float = 20.0, *, mass: float = 1.0, drag: float = 0.12, g: float = 9.81, fps: int = 30,
                 seconds: float = 4.0) -> dict:
    """Height and speed of a falling body per frame. Drag force = drag * v^2 (kg/m); the body stops at the ground."""
    np = need("numpy")
    need("scipy")
    import scipy.integrate as integrate

    def motion(_t, state):
        y, v = state                      # v is downward speed
        return [-v, g - (drag / mass) * v * abs(v)]

    def ground(_t, state):
        return state[0]
    ground.terminal, ground.direction = True, -1

    frames = int(round(seconds * fps)) + 1
    times = np.arange(frames) / fps
    sol = integrate.solve_ivp(motion, (0.0, float(times[-1]) + 5.0), [height, 0.0], events=ground, dense_output=True,
                              max_step=1.0 / fps, rtol=1e-8, atol=1e-10)
    t_ground = float(sol.t_events[0][0]) if len(sol.t_events[0]) else None
    y_drag, v_drag = [], []
    for t in times:
        if t_ground is not None and t >= t_ground:
            y_drag.append(0.0)
            v_drag.append(0.0)
        else:
            y, v = sol.sol(t)
            y_drag.append(max(0.0, float(y)))
            v_drag.append(float(v))
    y_free = np.maximum(0.0, height - 0.5 * g * times ** 2)
    t_free = float(np.sqrt(2 * height / g))
    terminal = float(np.sqrt(mass * g / drag)) if drag > 0 else None
    return clean({"fps": fps, "height": height, "g": g, "drag": drag, "mass": mass, "t": times, "y_drag": y_drag, "v_drag": v_drag,
                  "y_free": y_free, "t_ground_drag": t_ground, "t_ground_free": t_free, "terminal_speed": terminal,
                  "computed_by": "scipy.integrate.solve_ivp (drag) and numpy (no drag)"})


def wave(*, amplitude: float = 1.0, wavelength: float = 2.0, frequency: float = 0.5, length: float = 6.0, points: int = 181,
         fps: int = 30, seconds: float = 4.0) -> dict:
    """Two equal waves moving in opposite directions and their sum (a standing wave with fixed nodes), per frame."""
    np = need("numpy")
    x = np.linspace(0.0, length, points)
    k, w = 2 * np.pi / wavelength, 2 * np.pi * frequency
    frames = int(round(seconds * fps))
    right, left, total = [], [], []
    for n in range(frames):
        t = n / fps
        a = amplitude * np.sin(k * x - w * t)
        b = amplitude * np.sin(k * x + w * t)
        right.append(a)
        left.append(b)
        total.append(a + b)
    nodes = [float(v) for v in np.arange(0.0, length + 1e-9, wavelength / 2)]
    return clean({"fps": fps, "x": x, "right": right, "left": left, "sum": total, "nodes": nodes, "amplitude": amplitude,
                  "wavelength": wavelength, "frequency": frequency, "computed_by": "numpy"}, 3)
