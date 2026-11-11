"""The scene-plan language (Phase 1, part B2; agreement of 3 November 2026, decision 3).

A scene plan (``bie.scene-plan/1``) is what BIE's director writes: scenes over narration lines, each a list of
steps in the vocabulary of ``plan_vocab.json`` — people, things (saanche or fetched assets), texts, marks, arrows,
bubbles, cameras, and actions (pose, walk, give, hold, …). Every time in a plan is a cue into the narration
(``{"line", "word", …}`` or ``{"line", "edge"}``), so the same plan lands on real voice durations the day the voice
step writes them; a bare number of seconds is allowed only to nudge (the gold example uses a few).

``compile_plan`` turns a plan and a Timeline into the engine's show-spec (``bie.show-spec/1``) or refuses with every
problem named exactly (the step, the field, the reason), so the director can fix its plan without guessing. The
checks of the agreement run on the compiled spec: cue words must exist, every saancha parameter must fit the
manifest (part B1), every text must stay readable after the camera (CV-17), nothing may sit in the subtitle strip,
texts must not cover each other, and no stretch of SHOW_GAP seconds may show only text.

The Money v2 gold plan (``bie/brain/gold/money_v2``) is written in this language through ``Recorder`` and is the
example the director imitates (Claude's demo, not BIE output).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

FLOOR_PX = 36.0            # CV-17: the readable floor on the 1080p frame, measured after the camera
SUB_TOP = 960.0            # the subtitle strip: texts stay above this line on the 1080 stage
SHOW_GAP = 2.0             # agreement: no SHOW_GAP seconds without the thing being shown
BACKDROPS = {"world"}      # a whole place behind the lesson: it never counts as the thing being shown (so is a world3d)
AT_OPS = ("person", "item", "text", "mark", "glow")      # steps that may stand at a 3D model's spot instead of an x, y
VOCAB_PATH = Path(__file__).resolve().parent / "engine" / "plan_vocab.json"

POSES = {"stand": (8, 5, 8, 5), "give": (80, 0, 10, 5), "receive": (62, 18, 10, 5), "hold": (20, 85, 10, 5),
         "holdBoth": (22, 80, 22, 80), "think": (28, 145, 10, 5), "point": (120, 5, 10, 5), "shrug": (40, 110, 40, 110),
         "wave": (150, 25, 10, 5), "carry": (160, 40, 10, 5), "write": (35, 75, 10, 5), "walk": (10, 5, 10, 5),
         "refuse": (55, 105, 10, 5)}


class PlanProblems(ValueError):
    """A plan the compiler refuses: ``problems`` names every wrong step exactly."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__("the plan has problems:\n- " + "\n- ".join(self.problems))


def vocab() -> dict:
    return json.loads(VOCAB_PATH.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- times


class Cue:
    """A symbolic time in the narration, resolved against a Timeline; arithmetic keeps the symbol."""

    def __init__(self, line, word=None, nth=1, frac=0.0, edge=None, plus=0.0, value=0.0):
        self.line, self.word, self.nth, self.frac, self.edge, self.plus, self.value = line, word, nth, frac, edge, plus, value

    def to_json(self):
        out = {"line": self.line}
        if self.edge:
            out["edge"] = self.edge
        else:
            if self.word is not None:
                out["word"] = self.word
            if self.nth != 1:
                out["nth"] = self.nth
            if self.frac:
                out["frac"] = round(self.frac, 3)
        if self.plus:
            out["plus"] = round(self.plus, 3)
        return out

    def _shift(self, d):
        return Cue(self.line, self.word, self.nth, self.frac, self.edge, self.plus + d, self.value + d)

    def __add__(self, d):
        return self._shift(float(d))

    def __radd__(self, d):
        return self._shift(float(d))

    def __sub__(self, d):
        return self._shift(-float(d))

    def __float__(self):
        return float(self.value)

    def __lt__(self, other):
        return float(self) < float(other)

    def __le__(self, other):
        return float(self) <= float(other)

    def __gt__(self, other):
        return float(self) > float(other)

    def __ge__(self, other):
        return float(self) >= float(other)


def cues(T):
    """The gold builder's pen for times: ``C(line, word, frac=, nth=)`` -> a Cue carrying its resolved seconds."""

    def C(line, word=None, frac=0.0, nth=1):
        return Cue(line, word, nth, frac, value=T.cue(line, word, frac=frac, nth=nth))

    def start(line, plus=0.0):
        return Cue(line, edge="start", plus=plus, value=T.L(line)["t0"] + plus)

    def end(line, plus=0.0):
        return Cue(line, edge="end", plus=plus, value=T.L(line)["t1"] + plus)

    return C, start, end


def resolve_time(v, T, where, problems):
    """A plan time -> seconds: a number, or a cue dict; a wrong one lands in ``problems`` with its place."""
    if v is None:
        return None
    if isinstance(v, bool):
        problems.append(f"{where}: a time cannot be {v!r}")
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, Cue):
        return float(v)
    if isinstance(v, dict) and v.get("line"):
        plus = float(v.get("plus", 0.0))
        try:
            if v.get("edge"):
                if v["edge"] not in ("start", "end"):
                    problems.append(f"{where}: edge must be start or end, not {v['edge']!r}")
                    return None
                return T.L(v["line"])["t0" if v["edge"] == "start" else "t1"] + plus
            return T.cue(v["line"], v.get("word"), frac=float(v.get("frac", 0.0)), nth=int(v.get("nth", 1))) + plus
        except KeyError as exc:
            problems.append(f"{where}: {exc.args[0] if exc.args else exc}")
            return None
    problems.append(f"{where}: not a time: {v!r} (a number of seconds, or {{line, word}} / {{line, edge}})")
    return None


def _jsonable(v):
    if isinstance(v, Cue):
        return v.to_json()
    if isinstance(v, dict):
        return {k: _jsonable(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_jsonable(x) for x in v]
    if isinstance(v, float):
        return round(v, 3)
    return v


# ---------------------------------------------------------------- the recorder (what a plan writer holds)


class Recorder:
    """One scene of a plan, with the same hands as the compiler's executor: every call records one step."""

    def __init__(self, sid, lines, bg="paper", kicker=None, fg=None):
        self.id, self.lines, self.bg, self.kicker, self.fg = sid, lines, bg, kicker, fg
        self.steps, self.cam = [], []
        self.place3d = None

    def _step(self, op, **kw):
        self.steps.append({"op": op, **{k: v for k, v in kw.items() if v is not None or k in ("t1",)}})
        return self.steps[-1]

    # ---- elements (a person step returns the handle the action steps name)
    def person(self, pid, look, x=None, t0=None, y=885, h=440, facing=1, pose="stand", expr="smile", z=10, t1=None, at=None):
        self._step("person", id=pid, look=look, x=x, y=None if at else y, h=h, facing=facing, pose=pose, expr=expr, t0=t0, t1=t1,
                   z=z, at=at)
        return {"id": pid, "h": h}

    # ---- 3D (engine/three): the scene's 3D place, or a 3D model as a thing; ``at`` puts others beside its spots
    def world3d(self, model, p=None, steps=None, cam3d=None, id="world3d", enter="fade"):
        self.place3d = {k: v for k, v in dict(model=model, p=p, steps=steps, cam3d=cam3d, id=id, enter=enter).items() if v is not None}
        return {"id": id}

    def model(self, mid, model, x=960, y=540, p=None, t0=None, t1=None, s=1, z=20, w=None, h=None, steps=None, cam3d=None,
              keys=None, enter="fade"):
        thing = {"model": model, "p": p or {}}
        return self._step("item", thing=thing, id=mid, x=x, y=y, s=s, z=z, t0=t0, t1=t1, enter=enter, w=w, h=h, steps=steps,
                          cam3d=cam3d, keys=keys)

    def item(self, spec, x=None, y=None, t0=None, t1=None, s=1, z=20, keys=None, enter="pop", **kw):
        return self._step("item", thing=spec, x=x, y=y, s=s, z=z, t0=t0, t1=t1, enter=enter, keys=keys, **kw)

    def text(self, text, x=None, y=None, t0=None, t1=None, size=46, style="tag", w=None, z=40, **kw):
        return self._step("text", text=text, x=x, y=y, t0=t0, t1=t1, size=size, style=style, w=w, z=z, **kw)

    def mark(self, kind, x=None, y=None, t0=None, t1=None, w=120, z=45, **kw):
        return self._step("mark", kind=kind, x=x, y=y, t0=t0, t1=t1, w=w, z=z, **kw)

    def arrow(self, x1, y1, x2, y2, t0, t1=None, z=30, **kw):
        return self._step("arrow", x1=x1, y1=y1, x2=x2, y2=y2, t0=t0, t1=t1, z=z, **kw)

    def bubble(self, of, content, t0, t1=None, w=260, kind="think", dx=200, dy=-560, z=48, **kw):
        return self._step("bubble", of=of["id"], content=content, t0=t0, t1=t1, w=w, kind=kind, dx=dx, dy=dy, z=z, **kw)

    def rect(self, x, y, w, h, t0=None, t1=None, z=1, **kw):
        return self._step("rect", x=x, y=y, w=w, h=h, t0=t0, t1=t1, z=z, **kw)

    def glow(self, x=None, y=None, w=200, t0=None, t1=None, fill=None, z=5, **kw):
        return self._step("glow", x=x, y=y, w=w, t0=t0, t1=t1, fill=fill, z=z, **kw)

    def map(self, t0=None, z=1, **kw):
        return self._step("map", t0=t0, z=z, **kw)

    def camera(self, t, x=960, y=540, z=1.0, d=1.0):
        self.cam.append({"t": t, "d": d, "x": x, "y": y, "z": z})

    # ---- actions on a person
    def pose(self, p, t, pose):
        self._step("pose", who=p["id"], t=t, pose=pose)

    def expr(self, p, t, e):
        self._step("expr", who=p["id"], t=t, expr=e)

    def hold(self, p, t, spec):
        self._step("hold", who=p["id"], t=t, thing=spec)

    def walk(self, p, t, to_x, d=1.4):
        self._step("walk", who=p["id"], t=t, to_x=to_x, d=d)

    def face(self, p, t, s):
        self._step("face", who=p["id"], t=t, s=s)

    def shake(self, p, t, d=1.0):
        self._step("shake", who=p["id"], t=t, d=d)

    def nod(self, p, t, d=1.0):
        self._step("nod", who=p["id"], t=t, d=d)

    def give(self, spec, a, b, t, d=0.9, keep=True, z=70, drop_to=None):
        self._step("give", thing=spec, giver=a["id"], taker=b["id"], t=t, d=d, keep=keep, z=z,
                   drop_to=list(drop_to) if drop_to else None)

    def scene(self):
        out = {"id": self.id, "lines": list(self.lines), "bg": self.bg, "cam": _jsonable(self.cam),
               "steps": _jsonable(self.steps)}
        if self.kicker:
            out["kicker"] = self.kicker
        if self.fg:
            out["fg"] = self.fg
        if self.place3d:
            out["world3d"] = _jsonable(self.place3d)
        return out


def plan_of(recorders, video=None) -> dict:
    plan = {"schema": "bie.scene-plan/1", "scenes": [r.scene() for r in recorders]}
    if video:
        plan["video"] = video
    return plan


# ---------------------------------------------------------------- the executor (the v2 demo's Shot, moved here)


def hand(H, s, pose):
    a1, a2 = POSES.get(pose, POSES["stand"])[:2]
    r = math.radians
    sx, sy = 0.12 * H * s, -0.76 * H
    ex, ey = sx + math.sin(r(a1)) * 0.17 * H * s, sy + math.cos(r(a1)) * 0.17 * H
    return ex + math.sin(r(a1 + a2)) * 0.16 * H * s, ey + math.cos(r(a1 + a2)) * 0.16 * H


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def x_at(el, t):
    st = {"x": el.get("x", 0), "y": el.get("y", 0)}
    for k in el.get("keys", []):
        if t <= k["t"]:
            break
        p = ease((t - k["t"]) / k.get("d", 0.6))
        for f in ("x", "y"):
            if k.get(f) is not None:
                st[f] += (k[f] - st[f]) * p
    return st["x"], st["y"]


def facing_at(el, t):
    s = el.get("facing", 1)
    for f in el.get("facings", []):
        if t >= f["t"]:
            s = f["s"]
    return s


class _Executor:
    """Runs one scene's steps into engine elements; every wrong field lands in ``problems`` with its place."""

    def __init__(self, scene, T, problems):
        self.sc, self.T, self.problems = scene, T, problems
        self.id = scene.get("id", "?")
        first = scene["lines"][0]
        self.t0 = T.L(first)["t0"] - 0.35
        self.els, self.cam, self.people = [], [], {}
        self.models = {}                              # 3D models of this scene by id (world3d first), for ``at``
        if scene.get("world3d") is not None:
            self._world3d(scene["world3d"])

    def where(self, i, op):
        return f"scene {self.id} step {i + 1} ({op})"

    def rt(self, v, where, default=None):
        if v is None:
            return default
        return resolve_time(v, self.T, where, self.problems)

    def run(self, i, st):
        op = st.get("op")
        w = self.where(i, op or "?")
        fn = getattr(self, "op_" + str(op), None)
        if fn is None:
            known = sorted(n[3:] for n in dir(self) if n.startswith("op_"))
            self.problems.append(f"{w}: no step '{op}' (steps: {', '.join(known)})")
            return
        extras = {k: v for k, v in st.items() if k != "op"}
        try:
            fn(w, extras)
        except KeyError as exc:
            self.problems.append(f"{w}: missing field {exc}")

    def _person_of(self, w, extras):
        pid = extras.pop("who")
        p = self.people.get(pid)
        if p is None:
            self.problems.append(f"{w}: no person '{pid}' in this scene (it has: {', '.join(self.people) or 'none'})")
        return p

    # ---- 3D models (engine/three, models3d.py)
    def _model_el(self, w, spec, e, place):
        from bie.brain.video import models3d
        name = spec.get("model")
        mid = e.pop("id", None) or ("world3d" if place else f"model{len(self.models) + 1}")
        if mid in self.models:
            self.problems.append(f"{w}: two 3D models named '{mid}' in one scene")
        extra = sorted(set(spec) - {"model", "p"})
        if extra:
            self.problems.append(f"{w}: a 3D model thing has only model and p, not {', '.join(extra)}")
        size = models3d.PLACE_SIZE if place else (models3d.size_of(name) if isinstance(name, str) and models3d.get(name) else models3d.PLACE_SIZE)
        steps = e.pop("steps", None) or []
        if not isinstance(steps, list):
            self.problems.append(f"{w}: steps must be a list of [{{t, p, d}}]")
            steps = []
        cams = e.pop("cam3d", None) or []
        el = {"kind": "model3d", "id": mid, "model": name, "p": dict(spec.get("p") or {}) if isinstance(spec.get("p"), dict) else spec.get("p"),
              "x": e.pop("x", 960), "y": e.pop("y", 540), "w": e.pop("w", None) or size[0], "h": e.pop("h", None) or size[1],
              "s": e.pop("s", 1), "z": e.pop("z", 0 if place else 20), "t0": self.rt(e.pop("t0", None), w, self.t0),
              "t1": self.rt(e.pop("t1", None), w), "enter": e.pop("enter", "fade"), "keys": self._keys(w, e.pop("keys", None)),
              "steps": [dict(st, t=self.rt(st.get("t"), w + " steps", self.t0)) if isinstance(st, dict) else st for st in steps],
              "cam3d": [dict(k, t=self.rt(k.get("t"), w + " cam3d", self.t0)) if isinstance(k, dict) else k for k in cams]
              if isinstance(cams, list) else cams, "place": place}
        if el["enter"] not in ("pop", "fade", "none"):
            self.problems.append(f"{w}: enter must be pop, fade or none, not {el['enter']!r}")
        self._leftover(w, e)
        self.models[mid] = el
        self.els.append(el)
        return el

    def _world3d(self, spec):
        w = f"scene {self.id} world3d"
        if not isinstance(spec, dict) or not spec.get("model"):
            self.problems.append(f"{w}: world3d needs {{model, p, steps, cam3d}} (models: see the 3D library)")
            return
        e = {k: v for k, v in spec.items() if k not in ("model", "p")}
        e.setdefault("z", 0)
        for key in ("x", "y", "w", "h", "s", "keys"):
            if key in e:
                self.problems.append(f"{w}: a scene's 3D place always fills the stage; no field '{key}' here")
                e.pop(key)
        self._model_el(w, {"model": spec["model"], "p": spec.get("p") or {}}, e, True)

    def _at(self, w, e, el):
        """``at: {of, spot, dx, dy, when}`` instead of x and y: the element stands where a 3D model's spot is on the stage
        at ``when`` (default: when the element appears), measured from the engine's own description of that model (a
        model of this scene, named before this step; ``of`` may be left out when the scene has one)."""
        from bie.brain.video import models3d
        at = e.pop("at", None)
        if at is None:
            return
        if not isinstance(at, dict) or not at.get("spot"):
            self.problems.append(f"{w}: at needs {{of, spot, dx, dy, when}} (a 3D model's id and one of its spots)")
            return
        bad = sorted(set(at) - {"of", "spot", "dx", "dy", "when"})
        if bad:
            self.problems.append(f"{w}: at has no field {', '.join(repr(b) for b in bad)} (of, spot, dx, dy, when)")
        of = at.get("of")
        if of is None and len(self.models) == 1:
            of = next(iter(self.models))
        model = self.models.get(of)
        if model is None:
            self.problems.append(f"{w}: at.of: no 3D model '{of}' in this scene before this step (it has: {', '.join(self.models) or 'none'})")
            return
        if models3d.get(model.get("model")) is None or not isinstance(model.get("p"), dict):
            return                                         # the model's own problem is named once, by the checks
        t = self.rt(at.get("when"), w + " at.when", None) if at.get("when") is not None else el.get("t0")
        t = float(t if t is not None else model.get("t0") or 0.0)
        try:
            res = models3d.measure(model, t)
        except models3d.ModelsUnavailable as exc:
            self.problems.append(f"{w}: the spot could not be measured: {exc}")
            return
        if res.get("error"):
            self.problems.append(f"{w}: the 3D model '{of}' could not be measured: {res['error']}")
            return
        spot = (res.get("spots") or {}).get(at["spot"])
        if spot is None:
            self.problems.append(f"{w}: the 3D model '{of}' ({model['model']}) has no spot '{at['spot']}' at {t:.1f}s "
                                 f"(spots: {', '.join(sorted(res.get('spots') or {}))})")
            return
        if not spot.get("front"):
            self.problems.append(f"{w}: the spot '{at['spot']}' of '{of}' is hidden from its camera at {t:.1f}s (behind the model "
                                 "or the camera): turn the model (face, turn) or the camera, or use another spot")
        for f, d in (("x", "dx"), ("y", "dy")):
            v = at.get(d) or 0
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                self.problems.append(f"{w}: at.{d} needs a number of pixels, not {v!r}")
                v = 0
            el[f] = round(spot[f] + float(v), 1)
        el["on"] = of

    # ---- element ops
    def op_person(self, w, e):
        pid = e.pop("id")
        if pid in self.people:
            self.problems.append(f"{w}: two persons named '{pid}' in one scene")
        if "at" not in e and "x" not in e:
            raise KeyError("x")
        el = {"id": pid, "kind": "person", "look": e.pop("look"), "x": e.pop("x", 0), "y": e.pop("y", 885),
              "h": e.pop("h", 440), "facing": e.pop("facing", 1), "pose": e.pop("pose", "stand"),
              "expr": e.pop("expr", "smile"), "t0": self.rt(e.pop("t0", None), w, self.t0), "t1": self.rt(e.pop("t1", None), w),
              "z": e.pop("z", 10), "poses": [], "exprs": [], "holds": [], "facings": [], "walks": [], "shakes": [], "nods": [], "keys": []}
        self._at(w, e, el)
        self._leftover(w, e)
        self.people[pid] = el
        self.els.append(el)

    def _keys(self, w, keys):
        out = []
        for k in keys or []:
            k = dict(k)
            k["t"] = self.rt(k.get("t"), w + " keys", self.t0)
            out.append(k)
        return out

    def _xy_needed(self, e):
        if "at" not in e:
            for f in ("x", "y"):
                if f not in e:
                    raise KeyError(f)

    def op_item(self, w, e):
        spec = e.pop("thing")
        if isinstance(spec, dict) and "model" in spec:
            self._model_el(w, spec, e, False)
            return
        self._xy_needed(e)
        at = e.pop("at", None)
        el = dict(spec, x=e.pop("x", 0), y=e.pop("y", 0), s=e.pop("s", 1), z=e.pop("z", 20),
                  t0=self.rt(e.pop("t0", None), w, self.t0), t1=self.rt(e.pop("t1", None), w),
                  enter=e.pop("enter", "pop"), keys=self._keys(w, e.pop("keys", None)))
        if at is not None:
            self._at(w, {"at": at}, el)
        el.update(self._steps_times(w, e))
        self.els.append(el)

    def _steps_times(self, w, e):
        if "steps" in e and e["steps"]:
            e["steps"] = [dict(s, t=self.rt(s.get("t"), w + " steps", self.t0)) for s in e["steps"]]
        return e

    def op_text(self, w, e):
        self._xy_needed(e)
        el = {"text": e.pop("text"), "size": e.pop("size", 46), "style": e.pop("style", "tag"), "x": e.pop("x", 0), "y": e.pop("y", 0),
              "t0": self.rt(e.pop("t0", None), w, self.t0), "t1": self.rt(e.pop("t1", None), w), "z": e.pop("z", 40)}
        self._at(w, e, el)
        if e.get("w") is None:
            e.pop("w", None)
        el.update(self._steps_times(w, e))
        self.els.append(el)

    def op_mark(self, w, e):
        self._xy_needed(e)
        el = {"kind": "mark", "mark": e.pop("kind"), "x": e.pop("x", 0), "y": e.pop("y", 0), "w": e.pop("w", 120),
              "t0": self.rt(e.pop("t0", None), w, self.t0), "t1": self.rt(e.pop("t1", None), w), "z": e.pop("z", 45), "enter": "none"}
        self._at(w, e, el)
        self.els.append(dict(el, **e))

    def op_arrow(self, w, e):
        self.els.append(dict({"kind": "arrow", "x1": e.pop("x1"), "y1": e.pop("y1"), "x2": e.pop("x2"), "y2": e.pop("y2"),
                              "x": 0, "y": 0, "t0": self.rt(e.pop("t0", None), w, self.t0),
                              "t1": self.rt(e.pop("t1", None), w), "z": e.pop("z", 30), "enter": "none"}, **e))

    def op_bubble(self, w, e):
        dx = e.pop("dx", 200)
        self.els.append(dict({"kind": "bubble", "of": e.pop("of"), "content": e.pop("content"), "w": e.pop("w", 260),
                              "kind2": e.pop("kind", "think"), "t0": self.rt(e.pop("t0", None), w),
                              "t1": self.rt(e.pop("t1", None), w), "dx": dx, "dy": e.pop("dy", -560),
                              "z": e.pop("z", 48), "tail": -1 if dx > 0 else 1, "x": 0, "y": 0}, **e))

    def op_rect(self, w, e):
        self.els.append(dict({"kind": "rect", "x": e.pop("x"), "y": e.pop("y"), "w": e.pop("w"), "h": e.pop("h"),
                              "t0": self.rt(e.pop("t0", None), w, self.t0), "t1": self.rt(e.pop("t1", None), w),
                              "z": e.pop("z", 1), "enter": "fade"}, **e))

    def op_glow(self, w, e):
        self._xy_needed(e)
        el = {"kind": "glow", "x": e.pop("x", 0), "y": e.pop("y", 0), "w": e.pop("w"),
              "t0": self.rt(e.pop("t0", None), w, self.t0), "t1": self.rt(e.pop("t1", None), w), "z": e.pop("z", 5)}
        self._at(w, e, el)
        self.els.append(dict(el, **e))

    def op_map(self, w, e):
        self.els.append(dict({"kind": "map", "x": 0, "y": 0, "t0": self.rt(e.pop("t0", None), w, self.t0),
                              "z": e.pop("z", 1), "enter": e.pop("enter", "fade")}, **e))

    # ---- action ops
    def op_pose(self, w, e):
        p = self._person_of(w, e)
        pose = e.pop("pose")
        if pose not in POSES:
            self.problems.append(f"{w}: no pose '{pose}' (poses: {', '.join(sorted(POSES))})")
        if p is not None:
            p["poses"].append({"t": self.rt(e.pop("t"), w), "pose": pose})

    def op_expr(self, w, e):
        p = self._person_of(w, e)
        if p is not None:
            p["exprs"].append({"t": self.rt(e.pop("t"), w), "expr": e.pop("expr")})

    def op_hold(self, w, e):
        p = self._person_of(w, e)
        if p is not None:
            p["holds"].append({"t": self.rt(e.pop("t"), w), "item": e.pop("thing")})

    def op_walk(self, w, e):
        p = self._person_of(w, e)
        if p is None:
            return
        t, to_x, d = self.rt(e.pop("t"), w), e.pop("to_x"), e.pop("d", 1.4)
        x, _ = x_at(p, t)
        p["facings"].append({"t": t, "s": 1 if to_x > x else -1})
        p["keys"].append({"t": t, "d": d, "x": to_x})
        p["walks"].append({"t": t, "d": d})
        p["poses"].append({"t": t, "pose": "walk"})

    def op_face(self, w, e):
        p = self._person_of(w, e)
        if p is not None:
            p["facings"].append({"t": self.rt(e.pop("t"), w), "s": e.pop("s")})

    def op_shake(self, w, e):
        p = self._person_of(w, e)
        if p is not None:
            p["shakes"].append({"t": self.rt(e.pop("t"), w), "d": e.pop("d", 1.0)})

    def op_nod(self, w, e):
        p = self._person_of(w, e)
        if p is not None:
            p["nods"].append({"t": self.rt(e.pop("t"), w), "d": e.pop("d", 1.0)})

    def op_give(self, w, e):
        a = self.people.get(e.get("giver"))
        b = self.people.get(e.get("taker"))
        for key in ("giver", "taker"):
            if self.people.get(e[key]) is None:
                self.problems.append(f"{w}: no person '{e[key]}' in this scene")
        t = self.rt(e["t"], w)
        if a is None or b is None or t is None:
            return
        spec, d, keep, z, drop_to = e["thing"], e.get("d", 0.9), e.get("keep", True), e.get("z", 70), e.get("drop_to")
        a["poses"].append({"t": t - 0.4, "pose": "give"})
        sa = facing_at(a, t)
        ax, ay = x_at(a, t)
        hx, hy = hand(a["h"], sa, "give")
        bx, by = x_at(b, t + d)
        sb = facing_at(b, t + d)
        rx, ry = hand(b["h"], sb, "receive")
        a["holds"].append({"t": t, "item": None})
        end = (bx + rx, by + ry) if drop_to is None else tuple(drop_to)
        mv = dict({"group": [spec]}, x=ax + hx, y=ay + hy, s=1, z=z, enter="none",
                  t0=t, t1=t + d + (0.05 if keep or drop_to is None else 99),
                  keys=[{"t": t, "d": d, "x": end[0], "y": end[1]}])
        self.els.append(mv)
        a["poses"].append({"t": t + 0.55, "pose": "stand"})
        if drop_to is None:
            b["poses"].append({"t": t + 0.15, "pose": "receive"})
            if keep:
                b["poses"].append({"t": t + d, "pose": "hold"})
                b["holds"].append({"t": t + d, "item": spec})
            else:
                b["poses"].append({"t": t + d + 0.2, "pose": "stand"})
        else:
            mv["t1"] = None

    def _leftover(self, w, e):
        for key in e:
            self.problems.append(f"{w}: no field '{key}' here")


# ---------------------------------------------------------------- the compiler


def compile_plan(plan, T, *, width=1280, height=720, assets=None, checks=True, language=None, box_rule=True) -> dict:
    """A scene plan + a Timeline -> the engine's show-spec, or ``PlanProblems`` naming every wrong step."""
    problems = []
    shots = []
    for scene in plan.get("scenes", []):
        if not scene.get("lines"):
            problems.append(f"scene {scene.get('id', '?')}: no lines")
            continue
        missing = [l for l in scene["lines"] if not T.has(l)]
        if missing:
            problems.append(f"scene {scene.get('id', '?')}: no narration line {', '.join(missing)}")
            continue
        ex = _Executor(scene, T, problems)
        for i, st in enumerate(scene.get("steps", [])):
            ex.run(i, st)
        for c in scene.get("cam", []):
            ex.cam.append({"t": resolve_time(c.get("t"), T, f"scene {ex.id} camera", problems) or 0.0,
                           "d": c.get("d", 1.0), "x": c.get("x", 960), "y": c.get("y", 540), "z": c.get("z", 1.0)})
        shots.append(ex)
    for i, sh in enumerate(shots):
        sh.t1 = shots[i + 1].t0 if i + 1 < len(shots) else T.duration
    if shots:
        shots[0].t0 = 0.0
    scenes = []
    for sh in shots:
        out = {"id": sh.id, "t0": round(float(sh.t0), 3), "t1": round(float(sh.t1), 3), "bg": sh.bg if hasattr(sh, "bg") else None}
        out["bg"] = sh.sc.get("bg", "paper")
        out["cam"] = sh.cam
        out["els"] = [e for e in sh.els if e.get("h", 1) != 0]
        if sh.sc.get("fg"):
            out["fg"] = sh.sc["fg"]
        if sh.sc.get("kicker"):
            out["kicker"] = sh.sc["kicker"]
        scenes.append(out)
    spec = {"schema": "bie.show-spec/1", "fps": 30, "width": width, "height": height,
            "duration": round(T.duration, 3), "subs": T.subs(), "assets": assets or {}, "scenes": scenes}
    if checks:
        problems += check_spec(spec, plan, T, language=language, box_rule=box_rule)
    if problems:
        raise PlanProblems(problems)
    return spec


# ---------------------------------------------------------------- the checks (agreement of 3 November 2026, part B2)


def _cam_z(scene, t):
    z = 1.0
    for k in sorted(scene.get("cam", []), key=lambda k: k["t"]):
        if t < k["t"]:
            break
        p = ease((t - k["t"]) / max(0.01, k.get("d", 1.0)))
        z += (k.get("z", 1.0) - z) * p
    return z


def _text_box(el, t=None):
    """A rough box for a text element on the 1080 stage (the frame audit measures the real one)."""
    text = str(el.get("text", ""))
    if el.get("steps") and t is not None:
        for s in el["steps"]:
            if s.get("t") is not None and t >= s["t"] and s.get("text"):
                text = str(s["text"])
    size = float(el.get("size", 46))
    wrap = el.get("w")
    lines = [text]
    if wrap:
        per = max(1, int(wrap / (size * 0.56)))
        words, lines = text.split(), [""]
        for word in words:
            if lines[-1] and len(lines[-1]) + 1 + len(word) > per:
                lines.append(word)
            else:
                lines[-1] = (lines[-1] + " " + word).strip()
    w = max(len(l) for l in lines) * size * 0.56 + (28 if el.get("style") in ("tag", "pill") else 0)
    h = len(lines) * size * 1.25 + (16 if el.get("style") in ("tag", "pill") else 0)
    return el.get("x", 0) - w / 2, el.get("y", 0) - h / 2, w, h


def _visible(el, t, scene):
    t0 = el.get("t0") if el.get("t0") is not None else scene["t0"]
    t1 = el.get("t1") if el.get("t1") is not None else scene["t1"]
    return t0 <= t < min(t1, scene["t1"])


def _covers(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ox = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    oy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    return ox * oy > 0.25 * min(aw * ah, bw * bh)


def _nested_model(value) -> bool:
    if isinstance(value, dict):
        return "model" in value or any(_nested_model(v) for v in value.values())
    if isinstance(value, list):
        return any(_nested_model(v) for v in value)
    return False


def check_spec(spec, plan, T, language=None, box_rule=True) -> list:
    """The plan checks on the compiled spec; each problem names the scene, the text and the second."""
    from bie.brain import saanche

    problems = []

    def drawn(value, where):
        if isinstance(value, dict):
            if value.get("draw") and not str(value["draw"]).startswith("__"):
                for p in saanche.problems(value["draw"], value.get("p") or {}):
                    problems.append(f"{where}: {p}")
                for st in value.get("steps") or []:                  # a drawn thing's content changes: same law
                    if isinstance(st, dict) and isinstance(st.get("p"), dict):
                        for p in saanche.problems(value["draw"], st["p"]):
                            problems.append(f"{where}: step at {st.get('t')}: {p}")
                    if isinstance(st, dict) and "d" in st and not (isinstance(st["d"], (int, float)) and 0 <= st["d"] <= 30):
                        problems.append(f"{where}: step at {st.get('t')}: d must be 0-30 seconds (numbers glide over d)")
            for inner in value.values():
                drawn(inner, where)
        elif isinstance(value, list):
            for inner in value:
                drawn(inner, where)

    for scene in spec["scenes"]:
        sid = scene["id"]
        texts = [e for e in scene["els"] if e.get("text") is not None]
        things = [e for e in scene["els"] if e.get("text") is None and e.get("kind") != "rect"
                  and e.get("draw") not in BACKDROPS and not (e.get("kind") == "model3d" and e.get("place"))]
        from bie.brain.video import models3d
        for el in scene["els"]:
            if el.get("kind") == "model3d":
                problems.extend(models3d.element_problems(el, f"scene {sid} 3D model '{el.get('id')}'"))
        for el in scene["els"]:
            if el.get("kind") != "model3d" and _nested_model(el):
                problems.append(f"scene {sid}: a 3D model stands on its own (an item step or the scene's world3d), never inside "
                                "a group, a hold, a bubble or a give")
        panels = [e for e in scene["els"] if e.get("kind") == "rect" and e.get("fill") and e.get("alpha", 1.0) >= 0.85]
        drawn(scene["els"], f"scene {sid}")

        def hidden(el, t):
            """Behind an opaque panel at ``t``: not on screen, like on the drawn frame."""
            x, y, w, h = _text_box(el, t)
            for panel in panels:
                if _visible(panel, t, scene) and panel.get("z", 1) > (el.get("z", 40) or 40):
                    px, py = panel["x"] - panel["w"] / 2, panel["y"] - panel["h"] / 2
                    if x >= px - 4 and y >= py - 4 and x + w <= px + panel["w"] + 4 and y + h <= py + panel["h"] + 4:
                        return True
            return False

        # texts stay readable after the camera, and out of the subtitle strip
        for el in texts:
            t0 = el.get("t0") if el.get("t0") is not None else scene["t0"]
            t1 = min(el.get("t1") or scene["t1"], scene["t1"])
            shown = [t0 + k * 0.5 for k in range(int(max(0.0, t1 - t0) / 0.5) + 1)]
            shown = [t for t in shown if not hidden(el, t)]
            zmin = min((_cam_z(scene, t) for t in shown), default=1.0)
            size = float(el.get("size", 46))
            if shown and size * zmin < FLOOR_PX - 0.5:
                problems.append(f"scene {sid}: text '{el.get('text')}' is {size:.0f}px at camera {zmin:.2f} = "
                                f"{size * zmin:.0f}px on screen, under the {FLOOR_PX:.0f}px floor (CV-17)")
            x, y, w, h = _text_box(el)
            if spec.get("subs") and y + h > SUB_TOP and (el.get("z", 40) or 40) < 90:
                problems.append(f"scene {sid}: text '{el.get('text')}' reaches {y + h:.0f}, into the subtitle strip (>{SUB_TOP:.0f})")
        # texts must not cover each other for a second or more; no SHOW_GAP seconds of text alone (CV-17's audit rules)
        t = scene["t0"]
        bare_from = None
        covering = {}
        while t < scene["t1"]:
            on = [e for e in texts if _visible(e, t, scene) and not hidden(e, t)]
            now = set()
            for i, a in enumerate(on):
                for b in on[i + 1:]:
                    if _covers(_text_box(a, t), _text_box(b, t)):
                        pair = (str(a.get("text")), str(b.get("text")))
                        now.add(pair)
                        covering.setdefault(pair, [t, t])[1] = t
            for pair, (f, l) in list(covering.items()):
                if pair not in now:
                    if l - f + 0.5 >= 1.0:
                        problems.append(f"scene {sid}: '{pair[0]}' and '{pair[1]}' cover each other from {f:.1f}s for {l - f + 0.5:.1f}s")
                    del covering[pair]
            if any(_visible(e, t, scene) for e in things):
                bare_from = None
            elif bare_from is None:
                bare_from = t
            elif t - bare_from >= SHOW_GAP and on:
                problems.append(f"scene {sid}: only text on screen from {bare_from:.1f}s for {t - bare_from:.1f}s")
                bare_from = t  # one report per stretch
            t += 0.5
        for pair, (f, l) in covering.items():
            if l - f + 0.5 >= 1.0:
                problems.append(f"scene {sid}: '{pair[0]}' and '{pair[1]}' cover each other from {f:.1f}s for {l - f + 0.5:.1f}s")
    # every line is inside a scene (dikhane coverage: nothing spoken over no scene)
    seen = {l for sc in plan.get("scenes", []) for l in sc.get("lines", [])}
    missing = [l for l in T.line_ids() if l not in seen]
    if missing:
        problems.append(f"lines not in any scene: {', '.join(missing)}")
    # the box rule (Navin, 5 November 2026): texts off things, things off faces and words, the background's reserved
    # zones and the frame kept clear, words inside things readable, no caution line, Hindi labels in a Hindi video
    if box_rule:
        from bie.brain.video import box_rules
        problems += box_rules.problems(spec, language=language)
    return sorted(set(problems))
