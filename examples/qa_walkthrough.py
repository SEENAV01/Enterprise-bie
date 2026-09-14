"""Deterministic controlled source example; no real-book or media acceptance."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bie.director.script_plan import ScriptSegment, build_script_plan
from bie.director.voiceover_generation import generate_voiceover
from bie.director.qa_contract import snapshot_script, bind_span, ScriptClaim, SourcePage, SourcePassage, SourceCatalog
from bie.director.factual_script_qa import factual_qa
from bie.director.source_grounding_qa import source_grounding_qa, SourceBytes
from bie.director.lesson_architecture_contract import build_lesson_architecture, LessonSceneIntent
from bie.director.script_coherence_qa import coherence_qa, DiscourseBeat
from bie.director.repetition_detection import repetition_qa
from bie.director.age_level_qa import age_level_qa
from bie.director.speech_timing import estimate_speech
from bie.director.pause_timing import build_pause_timing
from bie.director.emphasis_timing import build_emphasis_timing
from bie.director.sync_contract import build_sync_context


def run():
    text = "A triangle has three straight sides."
    data = text.encode("utf-8")
    page = SourcePage("p1", "controlled-source", "sha256:" + hashlib.sha256(data).hexdigest(), 1, text, "utf8-fixture/1")
    passage = SourcePassage("e1", "p1", page.fingerprint(), "paragraph1", 0, len(text), text)
    catalog = SourceCatalog((page,), (passage,))
    script = build_script_plan("controlled-lesson", (ScriptSegment("u1", "s1", "EXPLAIN", "Explain triangles", ("e1",), ("o1",)),), "clear")
    draft = generate_voiceover("u1", (text,), {text: ("e1",)})
    snapshot = snapshot_script(script, (draft,), ("u1",))
    claims = (ScriptClaim("claim1", bind_span(snapshot, "u1"), "FACT", ("e1",)),)
    architecture = build_lesson_architecture("controlled-lesson", "Triangle fixture",
        (LessonSceneIntent("s1", "EXPLAIN", ("o1",), ("e1",)),), ("o1",), ("controlled-source",), "fixture/1")
    reports = (factual_qa(snapshot, claims, catalog), source_grounding_qa(snapshot, claims, catalog,
        (SourceBytes("controlled-source", data, "text/plain; charset=utf-8"),)),
        coherence_qa(snapshot, architecture, (DiscourseBeat("u1", snapshot.utterances[0].fingerprint(), ("triangle",)),)),
        repetition_qa(snapshot), age_level_qa(snapshot))
    speech = estimate_speech(snapshot.utterances)
    context = build_sync_context(speech, build_pause_timing(speech), build_emphasis_timing(speech))
    return {"scope": "Controlled UTF-8 source and DIR/TIME/SYNC/QA contracts only", "accepted": False,
        "actual_media_rendered": False, "real_book_executed": False,
        "snapshot_fingerprint": snapshot.fingerprint(), "sync_context_fingerprint": context.fingerprint(),
        "estimated_duration_ms": context.timeline.scenes[0].duration_ms,
        "reports": [{**asdict(r), "status": r.status, "accepted": r.accepted, "fingerprint": r.fingerprint()} for r in reports]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
