"""Small transparent synthetic fixtures; not real-book/empirical acceptance."""
from bie.director.script_plan import ScriptSegment, build_script_plan
from bie.director.voiceover_generation import generate_voiceover
from bie.director.speech_timing import (utterances_from_script, estimate_speech,
    align_reported_speech, ReportedAlignment)


def inputs(text="Money makes exchange easier.", uid="u", scene="s"):
    segment = ScriptSegment(uid, scene, "EXPLAIN", "Explain source claim, not a script.", ("e",), ("o",))
    script = build_script_plan("lesson", [segment], "teacher-v1")
    draft = generate_voiceover(uid, [text], {text: ("e",)})
    return utterances_from_script(script, [draft], [uid])


def speech(text="Money makes exchange easier.", wpm=120):
    return estimate_speech(inputs(text), wpm=wpm)


def measured():
    u = inputs("Money helps.")[0]
    a = ReportedAlignment(u.fingerprint(), "sha256:"+"a"*64, 2000,
                          ((100, 600), (1000, 1500)), "fixture-aligner/1")
    return align_reported_speech([u], [a])


def cue(boundary=1, ms=400, cid="p"):
    from bie.director.pause_timing import PauseCue
    return PauseCue(cid, "u", boundary, ms, "Source concept processing time", ("e",))


def anchor(start=0, end=1, strength=1.0, aid="a"):
    from bie.director.emphasis_plan import EmphasisDecision
    from bie.director.emphasis_timing import EmphasisAnchor
    return EmphasisAnchor(aid, "u", start, end,
                          EmphasisDecision("concept-exchange", strength, ("core concept",)), ("e",))


def target(seconds, scene="s"):
    from bie.director.pacing_plan import ScenePacing
    return ScenePacing(scene, seconds, "NORMAL", "Explicit test budget")


def empty_plans(s):
    from bie.director.pause_timing import build_pause_timing
    from bie.director.emphasis_timing import build_emphasis_timing
    return build_pause_timing(s), build_emphasis_timing(s)


def load(conceptual=0.0, novelty=0.0, notation=0.0):
    from bie.director.wpm_adaptation import ContentLoad
    return ContentLoad(conceptual, novelty, notation, ("e",))
