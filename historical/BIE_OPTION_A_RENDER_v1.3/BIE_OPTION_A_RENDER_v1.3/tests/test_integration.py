import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from bie_core.build import run

def test_canonical_pipeline_reaches_publish():
    ctx = run()
    assert not ctx.errors
    assert ctx.artifacts["qa_report"]["passed"] is True
    assert ctx.artifacts["publish"]["status"] == "PUBLISH_READY"

def test_traceable_stage_order():
    ctx = run()
    completed = [
        e["stage"] for e in ctx.events
        if e["status"] == "COMPLETED"
    ]
    expected = [
        "source","understanding","knowledge","planning","script",
        "scene","remotion","render","qa","publish"
    ]
    assert completed == expected
