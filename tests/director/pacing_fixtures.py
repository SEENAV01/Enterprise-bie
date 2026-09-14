"""Controlled timing inputs for pacing contract tests."""
from types import SimpleNamespace
from qa_fixtures import case
from bie.director.qa_contract import bind_span
from bie.director.speech_timing import estimate_speech, align_reported_speech
from bie.director.pause_timing import build_pause_timing
from bie.director.emphasis_timing import build_emphasis_timing
from bie.director.scene_duration_fit import fit_scene_durations
from bie.director.pacing_qa import PacingBeat, pacing_qa


def timed(texts=("A triangle has three straight sides.",), scene_ids=None, wpm=150, cues=(), alignments=None):
    c=case(texts,scene_ids=scene_ids)
    speech=estimate_speech(c.snapshot.utterances,wpm=wpm) if alignments is None else align_reported_speech(c.snapshot.utterances,alignments)
    pauses=build_pause_timing(speech,cues)
    emphasis=build_emphasis_timing(speech)
    timeline=fit_scene_durations(speech,pauses,emphasis)
    return SimpleNamespace(**vars(c),speech=speech,pauses=pauses,emphasis=emphasis,timeline=timeline)


def beat(c, uid="u1", mode="EXPLAIN", minimum=0, start=0, end=None, concepts=()):
    u=next(u for u in c.snapshot.utterances if u.utterance_id==uid)
    return PacingBeat("b:"+uid,bind_span(c.snapshot,uid,start,end),mode,concepts,u.evidence_ids,u.objective_ids,minimum)


def evaluate(c, beats=(), **kwargs):
    return pacing_qa(c.snapshot,c.speech,c.pauses,c.emphasis,c.timeline,beats,**kwargs)
