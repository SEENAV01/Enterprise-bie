"""METRIC-007: trusted objective/activity alignment and instructional sequence.
No NLP judgment or learner-effectiveness certification is implied.
"""
from ..models import BenchmarkError, ident
from ..domains.structured import record, choice, sequence
from .common import ids, indexed, weight
from .delivery_common import integer, interval, unknown, result_unit
KINDS={'explain','example','practice','assess'}
def measure(reference,candidate,artifacts):
    record(reference,{'duration_frames','objectives','content_bank'})
    record(candidate,{'activities'})
    duration=integer(reference['duration_frames'],1)
    goals=indexed(reference['objectives'],{'id','required_kinds','weight'},lower=1)
    bank=indexed(reference['content_bank'],{'id','objective_id','kind','feedback_ids'},lower=1)
    for r in goals.values():
        weight(r); required=ids(r['required_kinds'],lower=1)
        if not set(required)<=KINDS: raise BenchmarkError('UNKNOWN_ACTIVITY_KIND')
        if not {'explain','practice','assess'}<=set(required): raise BenchmarkError('WEAK_PEDAGOGY_REFERENCE')
    for r in bank.values():
        if ident(r['objective_id']) not in goals: raise BenchmarkError('UNKNOWN_REFERENCE_OBJECTIVE')
        choice(r['kind'],KINDS);ids(r['feedback_ids'])
        if r['kind'] in {'practice','assess'} and not r['feedback_ids']:
            raise BenchmarkError('REFERENCE_FEEDBACK_REQUIRED')
    # A malformed/incomplete trusted bank must not masquerade as a bad candidate.
    for key,g in goals.items():
        if not set(g['required_kinds']) <= {r['kind'] for r in bank.values() if r['objective_id']==key}:
            raise BenchmarkError('REFERENCE_ACTIVITY_COVERAGE_MISSING')
    rows=indexed(candidate['activities'],{'id','objective_id','content_id','kind','start','end','feedback_ids'})
    grouped={k:[] for k in goals}; spans=[]
    for key,r in rows.items():
        ident(r['objective_id']);ident(r['content_id']);choice(r['kind'],KINDS)
        if r['objective_id'] not in goals or r['content_id'] not in bank: raise BenchmarkError('UNKNOWN_CANDIDATE_ITEM')
        interval(r,duration);ids(r['feedback_ids']);grouped[r['objective_id']].append(r);spans.append((r['start'],r['end'],key))
    units=[]
    for key,g in sorted(goals.items()):
        reasons=[]; actions=sorted(grouped[key],key=lambda r:(r['start'],r['id']))
        if not set(g['required_kinds']) <= {r['kind'] for r in actions}: reasons.append('REQUIRED_ACTIVITY_MISSING')
        for r in actions:
            b=bank[r['content_id']]
            if (b['objective_id'],b['kind'])!=(key,r['kind']): reasons.append('CONTENT_ALIGNMENT_MISMATCH')
            if set(b['feedback_ids'])!=set(r['feedback_ids']): reasons.append('FEEDBACK_MAPPING_MISMATCH')
        for earlier,later in [('explain','example'),('explain','practice'),('example','practice'),('practice','assess')]:
            aa=[r for r in actions if r['kind']==earlier];bb=[r for r in actions if r['kind']==later]
            if aa and bb and min(r['end'] for r in aa)>min(r['start'] for r in bb): reasons.append('INSTRUCTIONAL_ORDER_VIOLATION')
        if len({r['content_id'] for r in actions})!=len(actions): reasons.append('REPEATED_CONTENT_CREDIT')
        units.append(result_unit(key,reasons,weight(g)))
    overlap=any(a[1]>b[0] for a,b in zip(sorted(spans),sorted(spans)[1:]))
    units.append(result_unit('activity-timeline',['OVERLAPPING_ACTIVITIES'] if overlap else []))
    return units,[],{'assessment_scope':'CURATED_OBJECTIVE_ACTIVITY_ALIGNMENT','learner_outcomes_measured':False}
