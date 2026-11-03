"""The Money v2 gold example (Claude's demo, not BIE output; agreement of 3 November 2026): the narration, its
timeline and the scene plan that BIE's AI learns from, emitting the showing engine's spec. Never a passed output."""
from .script_data import SCENES, EN2HI, build_script, to_say  # noqa: F401
from .timeline import Timeline  # noqa: F401
from .builder import ASSETS_USED, build_spec  # noqa: F401
import json
from pathlib import Path

MAP_PINS = {k: tuple(v) for k, v in json.loads(
    (Path(__file__).resolve().parents[2] / "video" / "engine" / "map_land.json").read_text(encoding="utf-8"))["pins"].items()}


def gold_spec(durations: dict | None = None, width: int = 1280, height: int = 720, assets: dict | None = None) -> dict:
    """The whole v2 show-spec (estimated timings when no voice durations are given)."""
    return build_spec(Timeline(build_script(), durations), MAP_PINS, width=width, height=height, assets=assets)
