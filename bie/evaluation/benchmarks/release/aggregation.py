"""RATER-005: conservative minimum across a pinned independent-rater roster.

Unknown and duplicate raters are errors; missing/blocked raters contribute zero.
Disagreement beyond an operator-pinned tolerance requires adjudication. No rater
can outvote a deterministic failure, nor can many clones inflate confidence.
"""
from fractions import Fraction
from ..models import BenchmarkError,exact_fields,ident,digest
from ..domains.structured import choice,sequence
from .contracts import context,assessment,score,keyed_rows

def aggregate(ctx,assessments,policy,*,expected_policy_sha256):
    from .contracts import pinned
    ctx=context(ctx);pinned(policy,expected_policy_sha256)
    exact_fields(policy,{'id','raters','maximum_disagreement'})
    ident(policy['id']);tolerance=score(policy['maximum_disagreement'])
    roster=keyed_rows(policy['raters'],{'id','kind','independence_group'},lower=1,upper=16)
    groups=set()
    for r in roster.values():
        choice(r['kind'],{'DETERMINISTIC','MODEL','HUMAN'});group=ident(r['independence_group'])
        if group in groups:raise BenchmarkError('DUPLICATE_RATER_INDEPENDENCE_GROUP')
        groups.add(group)
    if not any(r['kind']=='DETERMINISTIC' for r in roster.values()):raise BenchmarkError('DETERMINISTIC_RATER_REQUIRED')
    actual={}
    for row in sequence(assessments,lower=0,upper=16):
        assessment(row,ctx);key=row['assessor_id']
        if key not in roster or row['kind']!=roster[key]['kind']:raise BenchmarkError('UNEXPECTED_RATER')
        if key in actual:raise BenchmarkError('DUPLICATE_ASSESSMENT')
        actual[key]=row
    values=[];reasons=[]
    for key in sorted(roster):
        if key not in actual:values.append(Fraction(0));reasons.append('MISSING_REQUIRED_RATER')
        elif actual[key]['status']!='MEASURED':values.append(Fraction(0));reasons.append('REQUIRED_RATER_BLOCKED')
        else:values.append(score(actual[key]['score_exact']))
    spread=max(values)-min(values)
    if spread>tolerance:reasons.append('ADJUDICATION_REQUIRED')
    row={'context':ctx,'score_exact':str(min(values)),'status':'BLOCKED' if reasons else 'MEASURED',
         'reasons':sorted(set(reasons)),'spread_exact':str(spread),'policy_sha256':expected_policy_sha256,
         'assessment_sha256s':sorted(a['assessment_sha256'] for a in actual.values()),
         'rule':'MINIMUM_OF_REQUIRED_RATERS','release_authorized':False,'product_accepted':False}
    row['aggregate_sha256']=digest(row);return row
