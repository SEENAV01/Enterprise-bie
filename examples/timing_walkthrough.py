"""Executable synthetic DIR timing walkthrough; no real book/audio claim."""
from dataclasses import asdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bie.director.script_plan import ScriptSegment, build_script_plan
from bie.director.voiceover_generation import generate_voiceover
from bie.director.emphasis_plan import plan_emphasis
from bie.director.pacing_plan import ScenePacing
from bie.director.speech_timing import utterances_from_script, estimate_speech
from bie.director.pause_timing import PauseCue, build_pause_timing
from bie.director.emphasis_timing import EmphasisAnchor, build_emphasis_timing
from bie.director.scene_duration_fit import fit_scene_durations
from bie.director.wpm_adaptation import ContentLoad, adapt_wpm


def walkthrough():
    evidence = ("synthetic-fixture:exchange-definition",)
    text = "A medium of exchange helps people trade."
    script = build_script_plan("fixture-lesson", [ScriptSegment("segment-10", "exchange", "EXPLAIN",
        "Explain the definition and its role", evidence, ("objective:exchange",))], "teacher-v1")
    draft = generate_voiceover("segment-10", [text], {text: evidence})
    inputs = utterances_from_script(script, [draft], ["segment-10"])
    speech = estimate_speech(inputs, wpm=120)
    pauses = build_pause_timing(speech, [PauseCue("definition-pause", "segment-10", 4, 500,
        "Allow processing of the source definition", evidence)])
    decision = plan_emphasis([("concept:medium", 1.0, 0.8, 0.8)])[0]
    emphasis = build_emphasis_timing(speech, [EmphasisAnchor("definition", "segment-10", 1, 4, decision, evidence)])
    targets = [ScenePacing("exchange", 3.2, "NORMAL", "Illustrative preferred target, not a hard cap")]
    fit = fit_scene_durations(speech, pauses, emphasis, targets)
    adapted = adapt_wpm(speech, pauses, emphasis, ContentLoad(0.7, 0.4, 0.2, evidence), targets)
    return {
        "scope": "Synthetic recovered-contract walkthrough; NOT real-book or audio acceptance",
        "script": asdict(script), "voiceover": asdict(draft),
        "speech": asdict(speech), "pauses": asdict(pauses), "emphasis": asdict(emphasis),
        "scene_fit": asdict(fit), "adaptation": asdict(adapted),
        "fingerprints": {"script":script.fingerprint(), "speech":speech.fingerprint(),
                         "scene_fit":fit.fingerprint(), "adaptation":adapted.fingerprint()},
        "accepted": False,
    }


if __name__ == "__main__":
    print(json.dumps(walkthrough(), indent=2, ensure_ascii=False))
