"""RATER-004: paired observed agreement, exact binary Cohen kappa and score MAE.

Missing assessments block completeness. Degenerate kappa is explicitly UNDEFINED,
not coerced to perfect agreement. This module does not infer evaluator accuracy.
"""
from fractions import Fraction
from itertools import combinations
from ..models import BenchmarkError,exact_fields,ident,digest
from ..domains.structured import unique_ids,sequence
from .contracts import context,assessment,score,bounded_int,keyed_rows

def evaluate(contexts,assessments,*,assessor_ids,pass_threshold='1',minimum_pairs=2):
    expected={}
    for ctx in sequence(contexts,lower=1,upper=1000):
        ctx=context(ctx)
        if ctx['case_id'] in expected:raise BenchmarkError('DUPLICATE_CASE_CONTEXT')
        expected[ctx['case_id']]=ctx
    raters=unique_ids(assessor_ids,lower=2,upper=16);cutoff=score(pass_threshold);bounded_int(minimum_pairs,2,1000)
    if len(expected)<minimum_pairs:raise BenchmarkError('AGREEMENT_SAMPLE_TOO_SMALL')
    by_key={}
    for row in sequence(assessments,lower=0,upper=10000):
        assessment(row);key=(row['context']['case_id'],row['assessor_id'])
        if key[0] not in expected or key[1] not in raters:raise BenchmarkError('UNEXPECTED_ASSESSMENT')
        assessment(row,expected[key[0]])
        if key in by_key:raise BenchmarkError('DUPLICATE_ASSESSMENT')
        by_key[key]=row
    pairs=[];missing=[]
    for case in expected:
        for rater in raters:
            row=by_key.get((case,rater))
            if row is None or row['status']!='MEASURED':missing.append({'case_id':case,'assessor_id':rater})
    for a,b in combinations(sorted(raters),2):
        confusion=[[0,0],[0,0]];error=Fraction(0);n=0
        for case in sorted(expected):
            ra=by_key.get((case,a));rb=by_key.get((case,b))
            if not ra or not rb or ra['status']!='MEASURED' or rb['status']!='MEASURED':continue
            sa=score(ra['score_exact']);sb=score(rb['score_exact']);n+=1;error+=abs(sa-sb)
            confusion[int(sa>=cutoff)][int(sb>=cutoff)]+=1
        if n:
            observed=Fraction(confusion[0][0]+confusion[1][1],n)
            chance=sum(Fraction(sum(confusion[i]),n)*Fraction(sum(confusion[j][i] for j in range(2)),n) for i in range(2))
            kappa=None if chance==1 else str((observed-chance)/(1-chance))
        else:observed=chance=None;kappa=None
        pairs.append({'assessors':[a,b],'paired_count':n,'expected_count':len(expected),'confusion':confusion,
                      'observed_agreement':None if n==0 else str(observed),'chance_agreement':None if n==0 else str(chance),
                      'kappa':kappa,'kappa_state':'UNDEFINED' if kappa is None else 'DEFINED',
                      'mean_absolute_score_difference':None if n==0 else str(error/n)})
    return {'status':'BLOCKED' if missing else 'MEASURED','missing':sorted(missing,key=lambda x:(x['case_id'],x['assessor_id'])),
            'pairs':pairs,'pass_threshold':str(cutoff),'accuracy_inferred':False,'product_accepted':False}
