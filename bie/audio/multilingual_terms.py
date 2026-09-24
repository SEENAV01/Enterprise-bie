"""BIE-AUDIO-VO-006: explicit source-bound code-switching and term readings.

No automatic language inference or translation. Aliases/IPA are realized by
VO-002 first; this layer binds their spoken language without editing captions.
Splitting a transformed pronunciation or a segment's pause boundary is forbidden.
"""
from dataclasses import dataclass,replace
from .common import AudioError,boundary,digest,fingerprint,integer,locale,refs,text
from .speech_contract import SpeechPlan,SpeechSpan,records


@dataclass(frozen=True)
class LanguageTerm:
    utterance_id: str
    utterance_fingerprint: str
    start: int
    end: int
    original: str
    expected_spoken: str
    spoken_language: str
    evidence_refs: tuple[str,...]
    decision_id: str
    def __post_init__(self):
        text(self.utterance_id,'utterance',2048);digest(self.utterance_fingerprint)
        integer(self.start,'start');integer(self.end,'end',1)
        text(self.original,'term',8192);text(self.expected_spoken,'term speech',65536)
        if self.end-self.start!=len(self.original):raise AudioError('TERM_LENGTH')
        locale(self.spoken_language);refs(self.evidence_refs,'language evidence');text(self.decision_id,'decision',2048)


def apply_languages(plan: SpeechPlan, terms: tuple[LanguageTerm,...], *, expected_plan=None) -> SpeechPlan:
    if type(plan)is not SpeechPlan:raise AudioError('SPEECH_PLAN_REQUIRED')
    if expected_plan is not None and expected_plan!=plan.fingerprint():raise AudioError('STALE_LANGUAGE_PLAN')
    records(terms,LanguageTerm,'language terms',required=False)
    if len({x.decision_id for x in terms})!=len(terms):raise AudioError('DUPLICATE_LANGUAGE_DECISION')
    by={}
    for t in terms:by.setdefault(t.utterance_id,[]).append(t)
    for ts in by.values():
        ts.sort(key=lambda t:t.start)
        if any(a.end>b.start for a,b in zip(ts,ts[1:])):raise AudioError('OVERLAPPING_LANGUAGE_TERMS')
    output=[];used=set()
    for segment in plan.segments:
        own=[t for t in by.get(segment.utterance_id,[]) if t.start<segment.end and t.end>segment.start]
        parts=list(segment.spans)
        for t in own:
            if t.utterance_fingerprint!=segment.utterance_fingerprint:raise AudioError('STALE_LANGUAGE_TERM')
            if not segment.start<=t.start<t.end<=segment.end:raise AudioError('LANGUAGE_TERM_SPLIT_BY_SEGMENT')
            a,b=t.start-segment.start,t.end-segment.start
            if segment.display_text[a:b]!=t.original:raise AudioError('LANGUAGE_TERM_TEXT')
            if not boundary(segment.display_text,a) or not boundary(segment.display_text,b):raise AudioError('LANGUAGE_TERM_CLUSTER')
            pieces=[];reading=[]
            for p in parts:
                if p.end<=t.start or p.start>=t.end:pieces.append(p);continue
                left=max(p.start,t.start);right=min(p.end,t.end)
                if (left!=p.start or right!=p.end) and (p.kind!='literal' or p.original!=p.spoken or p.phonemes):
                    raise AudioError('LANGUAGE_TERM_SPLITS_READING')
                def cut(x,y,changed):
                    if x>=y:return
                    full=x==p.start and y==p.end
                    original=p.original[x-p.start:y-p.start]
                    spoken=p.spoken if full else original
                    target=replace(p,start=x,end=y,original=original,spoken=spoken)
                    if changed:
                        target=replace(target,language=t.spoken_language,rule_fingerprint=fingerprint((p.rule_fingerprint,t)),
                            source_refs=tuple(dict.fromkeys((*p.source_refs,*t.evidence_refs))))
                        reading.append(spoken)
                    pieces.append(target)
                cut(p.start,left,False);cut(left,right,True);cut(right,p.end,False)
            if ''.join(reading)!=t.expected_spoken:raise AudioError('LANGUAGE_TERM_SPEECH_MISMATCH')
            parts=pieces;used.add(t.decision_id)
        output.append(replace(segment,spans=tuple(parts)))
    if used!={x.decision_id for x in terms}:raise AudioError('UNKNOWN_LANGUAGE_TERM')
    # Reviews are not erased by declaring a language. They require upstream correction.
    return replace(plan,segments=tuple(output),language_policy_fingerprint=fingerprint(('language-terms/1',plan.language_policy_fingerprint,terms)))
