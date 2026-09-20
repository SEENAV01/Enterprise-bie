"""H2-003 explicit, frame-indexed visual-property contracts.

Unsupported specialized morph/camera/simulation actions are rejected instead of
being reduced to an inert metadata wrapper. Time domains are milliseconds;
translations/path points are CSS pixels in the element's containing box.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections.abc import Mapping
import math
from .animation_compiler_common import normalize_track, AnimationCompilerError
from .hardening_contracts import finite_number

SUPPORTED_ACTIONS = {"enter", "exit", "reveal", "emphasize", "transform", "path_follow"}


def fail(code, message):
    raise AnimationCompilerError(code + ": " + message)


def number(v, lo, hi, name):
    try:
        x = finite_number(v, name)
    except ValueError as exc:
        fail("ANIMATION_PARAMETER_INVALID", str(exc))
    if not lo <= x <= hi:
        fail("ANIMATION_PARAMETER_INVALID", name + " outside supported range")
    return x


@dataclass(frozen=True)
class MotionContract:
    track_id: str
    element_id: str
    action: str
    start_ms: int
    end_ms: int
    easing: str
    parameters: dict
    owned_properties: tuple[str, ...]
    accepted: bool = False

    def to_dict(self):
        return asdict(self)


def motion_contract(track) -> MotionContract:
    tid, eid, action, start, end, params, src, rsn = normalize_track(track)
    if action not in SUPPORTED_ACTIONS:
        fail("ANIMATION_ACTION_UNSUPPORTED", "no generic equivalent for action " + action)
    if end > 3600000:
        fail("ANIMATION_TIME_BOUNDS", "track interval exceeds one hour")
    allowed = {"easing"}
    if action in {"enter", "exit"}: allowed |= {"from_opacity", "to_opacity"}
    elif action == "reveal": allowed |= {"direction"}
    elif action == "emphasize": allowed |= {"peak_scale"}
    elif action == "transform": allowed |= {"from", "to"}
    elif action == "path_follow": allowed |= {"points", "coordinate_space"}
    if set(params) - allowed:
        fail("ANIMATION_PARAMETER_UNCONSUMED", "unsupported parameters: " + ", ".join(sorted(set(params)-allowed)))
    easing = params.get("easing", "linear")
    if not isinstance(easing,str) or easing not in {"linear", "smoothstep"}:
        fail("ANIMATION_EASING_UNSUPPORTED", "only linear and smoothstep are governed")
    p = {}
    if action in {"enter", "exit"}:
        p = {"from_opacity": number(params.get("from_opacity", 0 if action == "enter" else 1), 0, 1, "from_opacity"),
             "to_opacity": number(params.get("to_opacity", 1 if action == "enter" else 0), 0, 1, "to_opacity")}
        if p["from_opacity"] == p["to_opacity"]:
            fail("ANIMATION_NO_VISUAL_CHANGE", "opacity endpoints are identical")
        owned = ("opacity",)
    elif action == "reveal":
        direction = params.get("direction", "left")
        if not isinstance(direction,str) or direction not in {"left", "right", "up", "down"}:
            fail("ANIMATION_PARAMETER_INVALID", "invalid reveal direction")
        p = {"direction": direction}; owned = ("clipPath",)
    elif action == "emphasize":
        p = {"peak_scale": number(params.get("peak_scale", 1.1), 1.001, 3, "peak_scale")}; owned = ("scale",)
    elif action == "transform":
        a, b = params.get("from"), params.get("to")
        bounds = {"opacity": (0, 1), "translate_x": (-10000, 10000), "translate_y": (-10000, 10000), "scale": (.01, 100), "rotate": (-36000, 36000)}
        if not isinstance(a, Mapping) or not isinstance(b, Mapping) or not a or set(a) != set(b) or set(a)-set(bounds):
            fail("ANIMATION_TRANSFORM_INVALID", "from/to must have the same nonempty supported property set")
        p = {side: {k: number(values[k], *bounds[k], k) for k in sorted(values)} for side, values in (("from", a), ("to", b))}
        if p["from"] == p["to"]:
            fail("ANIMATION_NO_VISUAL_CHANGE", "transform endpoints are identical")
        owned = tuple(sorted({"translate" if k.startswith("translate_") else k for k in a}))
    else:
        if params.get("coordinate_space") != "pixels":
            fail("ANIMATION_PATH_SPACE_REQUIRED", "explicit containing-box pixels required")
        pts = params.get("points")
        if not isinstance(pts, (list, tuple)) or not 2 <= len(pts) <= 256:
            fail("ANIMATION_PATH_INVALID", "path needs 2..256 vertices")
        checked = []
        for pt in pts:
            if not isinstance(pt, (list, tuple)) or len(pt) != 2:
                fail("ANIMATION_PATH_INVALID", "each path point must be x,y")
            q = [number(v, -10000, 10000, "path coordinate") for v in pt]
            if checked and math.dist(checked[-1], q) < 1e-8:
                fail("ANIMATION_PATH_INVALID", "adjacent points must define a visible segment")
            checked.append(q)
        lengths = [math.dist(a, b) for a, b in zip(checked, checked[1:])]
        p = {"points": checked, "lengths": lengths, "total_length": sum(lengths), "coordinate_space": "pixels"}; owned = ("translate",)
    return MotionContract(tid, eid, action, start, end, easing, p, owned)


def frame_window(c: MotionContract, fps: int):
    if type(fps) is not int or not 1 <= fps <= 240:
        fail("ANIMATION_FPS_INVALID", "integer fps in 1..240 required")
    start, end = (c.start_ms*fps+500)//1000, (c.end_ms*fps+500)//1000-1
    if end <= start:
        fail("ANIMATION_FRAME_RANGE_COLLAPSES", "endpoints quantize to the same frame")
    if c.action == "emphasize" and end-start < 2:
        fail("ANIMATION_PULSE_UNSAMPLED", "emphasis requires at least three distinct frames")
    return start, end


def motion_state(c: MotionContract, frame: int, fps: int):
    if type(frame) is not int or frame < 0:
        fail("ANIMATION_FRAME_INVALID", "nonnegative integer frame required")
    a, b = frame_window(c, fps)
    u = min(1, max(0, (frame-a)/(b-a)))
    if c.easing == "smoothstep": u = u*u*(3-2*u)
    p = c.parameters
    if c.action in {"enter", "exit"}:
        return {"opacity": p["from_opacity"]+(p["to_opacity"]-p["from_opacity"])*u}
    if c.action == "reveal":
        index = {"left": 1, "right": 3, "up": 2, "down": 0}[p["direction"]]
        inset = [0., 0., 0., 0.]; inset[index] = 100*(1-u)
        return {"inset_percent": inset}
    if c.action == "emphasize":
        return {"scale": 1+(p["peak_scale"]-1)*(1-abs(2*u-1))}
    if c.action == "transform":
        return {k: p["from"][k]+(v-p["from"][k])*u for k, v in p["to"].items()}
    distance, covered = u*p["total_length"], 0.
    for i, length in enumerate(p["lengths"]):
        if distance <= covered+length or i == len(p["lengths"])-1:
            r = min(1, max(0, (distance-covered)/length))
            return {"translate_x": p["points"][i][0]+(p["points"][i+1][0]-p["points"][i][0])*r,
                    "translate_y": p["points"][i][1]+(p["points"][i+1][1]-p["points"][i][1])*r}
        covered += length
    fail("ANIMATION_PATH_INVALID", "unreachable empty path")
