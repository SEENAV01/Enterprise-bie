"""METRIC-008: beat coverage, focus, narration density and editorial timing.
Word-density is a declared whitespace-token diagnostic, not a multilingual TTS predictor.
"""
from fractions import Fraction
from ..models import BenchmarkError, ident, text
from ..domains.structured import record, sequence, amount
from .common import ids,indexed,weight
from .delivery_common import integer,interval,unknown,result_unit,covered

def measure(reference,candidate,artifacts):
    record(reference,{'duration_frames','fps','max_words_per_minute','max_parallel_focus','max_gap_frames','beats','precedence'})
    record(candidate,{'scenes'})
    duration=integer(reference['duration_frames'],1);fps=integer(reference['fps'],1,120)
    max_wpm=amount(reference['max_words_per_minute'],positive=True,maximum=600)
    max_focus=integer(reference['max_parallel_focus'],1,8);gap=integer(reference['max_gap_frames'],0,duration)
    beats=indexed(reference['beats'],{'id','kind','concept_id','weight'},lower=1)
    for b in beats.values(): ident(b['kind']);ident(b['concept_id']);weight(b)
    edges=[]
    for e in sequence(reference['precedence'],lower=0,upper=128):
        record(e,{'before','after'});edges.append((ident(e['before']),ident(e['after'])))
    from .common import topological
    topological(beats,edges)
    scenes=indexed(candidate['scenes'],{'id','start','end','beats','narration','focus_ids'})
    occurrences={k:[] for k in beats};sreasons={};spans=[]
    for key,s in scenes.items():
        a,b=interval(s,duration);spans.append((a,b,key));keys=ids(s['beats']);unknown(keys,beats)
        focus=ids(s['focus_ids']);text(s['narration']);reasons=[]
        if not set(focus)<={b['concept_id'] for b in beats.values()}:raise BenchmarkError('UNKNOWN_FOCUS_CONCEPT')
        if len(focus)>max_focus: reasons.append('TOO_MANY_SIMULTANEOUS_FOCI')
        if Fraction(len(s['narration'].split())*60*fps,b-a)>max_wpm: reasons.append('NARRATION_DENSITY_EXCEEDED')
        for k in keys:
            occurrences[k].append(s)
            if beats[k]['concept_id'] not in focus: reasons.append('BEAT_WITHOUT_CONCEPT_FOCUS')
        sreasons[key]=reasons
    units=[]
    for k,b in sorted(beats.items()):
        rows=occurrences[k];reasons=[]
        if not rows: reasons.append('REQUIRED_BEAT_MISSING')
        elif len(rows)!=1: reasons.append('DUPLICATE_BEAT')
        for s in rows: reasons.extend(sreasons[s['id']])
        for a,z in edges:
            if z==k and occurrences[a] and rows and max(s['end'] for s in occurrences[a])>min(s['start'] for s in rows):
                reasons.append('BEAT_PRECEDENCE_VIOLATION')
        units.append(result_unit(k,reasons,weight(b)))
    timeline=[]; ordered=sorted(spans)
    if any(a[1]>b[0] for a,b in zip(ordered,ordered[1:])): timeline.append('OVERLAPPING_SCENES')
    if not covered(0,duration,[(a,b) for a,b,k in spans],gap): timeline.append('UNCOVERED_NARRATIVE_TIME')
    # Scenes without scored beats must not bypass focus/density checks.
    timeline += [r for reasons in sreasons.values() for r in reasons]
    units.append(result_unit('scene-timeline',timeline))
    return units,[],{'assessment_scope':'STRUCTURED_EDITORIAL_PLAN','cinematic_quality_certified':False}
