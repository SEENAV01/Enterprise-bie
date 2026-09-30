"""PHY-002: explicit bounded Newtonian reference profiles, inertial frames."""
from __future__ import annotations
import math
from ..models import BenchmarkError, exact_fields, number
from .common import scalar, vector


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError("INVALID_FIELDS")
    op = data.get("op")
    if op == "constant_acceleration_1d":
        exact_fields(data, {"op", "x0", "v0", "a", "time"})
        x = scalar(data["x0"], "length")
        v = scalar(data["v0"], "speed")
        a = scalar(data["a"], "acceleration")
        t = scalar(data["time"], "time", nonnegative=True)
        return {"position_m": number(x + v*t + .5*a*t*t), "velocity_mps": number(v + a*t)}
    if op == "net_acceleration":
        exact_fields(data, {"op", "mass", "forces"})
        mass = scalar(data["mass"], "mass", positive=True)
        if type(data["forces"]) is not list or not 1 <= len(data["forces"]) <= 128:
            raise BenchmarkError("INVALID_FORCE_COUNT")
        forces = [vector(f, "force") for f in data["forces"]]
        return {"acceleration_mps2": [number(math.fsum(f[i] for f in forces) / mass) for i in range(3)]}
    if op == "perfectly_inelastic_1d":
        exact_fields(data, {"op", "mass1", "mass2", "velocity1", "velocity2"})
        m1 = scalar(data["mass1"], "mass", positive=True)
        m2 = scalar(data["mass2"], "mass", positive=True)
        u1 = scalar(data["velocity1"], "speed")
        u2 = scalar(data["velocity2"], "speed")
        v = (m1*u1 + m2*u2) / (m1 + m2)
        # Reduced-mass form avoids cancellation in the energy loss.
        loss = .5 * (m1*m2/(m1+m2)) * (u1-u2)**2
        return {"final_velocity_mps": number(v), "kinetic_energy_lost_J": number(loss)}
    if op == "constant_force_work":
        exact_fields(data, {"op", "force", "displacement"})
        f = vector(data["force"], "force")
        d = vector(data["displacement"], "length")
        return {"work_J": number(math.fsum(f[i]*d[i] for i in range(3)))}
    raise BenchmarkError("UNSUPPORTED_OPERATION")
