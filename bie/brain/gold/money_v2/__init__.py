"""The Money v2 gold example (Claude's demo, not BIE output; agreement of 3 November 2026): the narration, its
timeline and the scene plan that BIE's AI learns from, written in the scene-plan language (bie.scene-plan/1) and
compiled by bie/brain/video/showplan.py into the showing engine's spec. Never a passed output."""
from .script_data import SCENES, EN2HI, build_script, to_say  # noqa: F401
from .timeline import Timeline  # noqa: F401
from .builder import ASSETS_USED, build_plan  # noqa: F401
import json
from pathlib import Path

from bie.brain.video import showplan

MAP_PINS = {k: tuple(v) for k, v in json.loads(
    (Path(__file__).resolve().parents[2] / "video" / "engine" / "map_land.json").read_text(encoding="utf-8"))["pins"].items()}


def gold_plan(durations: dict | None = None):
    """The v2 plan in the scene-plan language, with the Timeline it was written against."""
    T = Timeline(build_script(), durations)
    return build_plan(T, MAP_PINS), T


def gold_spec(durations: dict | None = None, width: int = 1280, height: int = 720, assets: dict | None = None) -> dict:
    """The whole v2 show-spec: the gold plan compiled (estimated timings when no voice durations are given)."""
    plan, T = gold_plan(durations)
    return showplan.compile_plan(plan, T, width=width, height=height, assets=assets)
