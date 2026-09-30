"""PHY-003: linear waves; phase propagation is distinct from particle motion."""
from __future__ import annotations
import math
from ..models import BenchmarkError, exact_fields, number
from .common import integer, scalar


def solve(data: dict) -> dict:
    if type(data) is not dict:
        raise BenchmarkError("INVALID_FIELDS")
    op = data.get("op")
    if op == "wave_properties":
        exact_fields(data, {"op", "wavelength", "frequency"})
        wavelength = scalar(data["wavelength"], "length", positive=True)
        frequency = scalar(data["frequency"], "frequency", positive=True)
        return {"phase_speed_mps": number(wavelength*frequency),
                "omega_radps": number(2*math.pi*frequency), "k_radpm": number(2*math.pi/wavelength)}
    if op == "linear_superposition":
        exact_fields(data, {"op", "components"})
        if type(data["components"]) is not list or not 1 <= len(data["components"]) <= 128:
            raise BenchmarkError("INVALID_COMPONENT_COUNT")
        ys = []
        for component in data["components"]:
            exact_fields(component, {"amplitude", "phase"})
            a = scalar(component["amplitude"], "length", nonnegative=True)
            phase = scalar(component["phase"], "angle")
            if abs(phase) > 1e8:
                raise BenchmarkError("PHASE_RESOLUTION_LIMIT")
            ys.append(a*math.sin(phase))
        return {"displacement_m": number(math.fsum(ys))}
    if op == "traveling_wave_sample":
        exact_fields(data, {"op", "amplitude", "wavelength", "frequency", "position", "time", "phase", "direction"})
        a = scalar(data["amplitude"], "length", nonnegative=True)
        wavelength = scalar(data["wavelength"], "length", positive=True)
        frequency = scalar(data["frequency"], "frequency", positive=True)
        x = scalar(data["position"], "length")
        t = scalar(data["time"], "time", nonnegative=True)
        phase = scalar(data["phase"], "angle")
        if type(data["direction"]) is not str or data["direction"] not in {"POSITIVE_X", "NEGATIVE_X"}:
            raise BenchmarkError("INVALID_DIRECTION")
        sign = 1 if data["direction"] == "POSITIVE_X" else -1
        omega = 2*math.pi*frequency
        angle = 2*math.pi*x/wavelength - sign*omega*t + phase
        if abs(angle) > 1e8:
            raise BenchmarkError("PHASE_RESOLUTION_LIMIT")
        return {"displacement_m": number(a*math.sin(angle)),
                "particle_velocity_mps": number(-sign*omega*a*math.cos(angle)),
                "phase_velocity_mps": number(sign*wavelength*frequency)}
    if op == "fixed_string_mode":
        exact_fields(data, {"op", "length", "wave_speed", "mode"})
        length = scalar(data["length"], "length", positive=True)
        speed = scalar(data["wave_speed"], "speed", positive=True)
        n = integer(data["mode"], 1, 10000)
        return {"wavelength_m": number(2*length/n), "frequency_Hz": number(n*speed/(2*length)),
                "node_count_including_ends": n + 1}
    raise BenchmarkError("UNSUPPORTED_OPERATION")
