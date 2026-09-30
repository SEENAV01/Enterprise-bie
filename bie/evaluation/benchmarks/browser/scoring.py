"""H4-006: fixed denominator, UI feedback-path evidence, not learner outcomes."""
from fractions import Fraction
from ..models import BenchmarkError, digest

def grade(reference,observed):
    if type(observed) is not dict or observed.get('status')!='COLLECTED':raise BenchmarkError('BROWSER_OBSERVATION_INCOMPLETE')
    runs=observed.get('runs')
    if type(runs) is not list or len(runs)!=reference['replay_count']:raise BenchmarkError('BROWSER_REPLAY_INCOMPLETE')
    units=[]
    for step in reference['steps']:
        for check in step['checks']:
            ok=True; reasons=[]
            for run in runs:
                rows={r['step_id']:r for r in run['steps']}
                row=rows.get(step['id']); v=None if row is None else row['observations'].get(check['target'])
                good=bool(row and not row['action_error'] and v and v.get('present'))
                if good:
                    actual=v.get(check['property']);exp=check['expected']
                    good=(type(actual) in (int,float) and actual>=exp) if check['property']=='contrast_at_least' else (type(actual) is type(exp) and actual==exp)
                if not good:ok=False;reasons.append('OBSERVED_CHECK_MISMATCH')
            units.append({'id':check['id'],'weight':'1','credit':'1' if ok else '0','reasons':sorted(set(reasons))})
    runtime_ok=all(not run['events']['blocked_requests'] and not run['events']['page_errors']
                   and not run['events']['console_errors'] and not run['events']['violations']
                   and len(run['steps'])==len(reference['steps']) and not any(s['action_error'] for s in run['steps'])
                   for run in runs)
    units.append({'id':'runtime-health','weight':'1','credit':'1' if runtime_ok else '0',
                  'reasons':[] if runtime_ok else ['BROWSER_RUNTIME_ERROR']})
    if reference['replay_count']==2:
        from .replay import compare
        same=compare(runs[0],runs[1])['matches']
        units.append({'id':'fresh-context-replay','weight':'1','credit':'1' if same else '0',
                      'reasons':[] if same else ['BROWSER_REPLAY_DIVERGED']})
    by_id={u['id']:u for u in units};objective_reports=[]
    for obj in reference['objectives']:
        passed=all(by_id[c]['credit']=='1' for c in obj['checks'])
        objective_reports.append({'objective_id':obj['id'],'concept_id':obj['concept_id'],
          'source_sha256':obj['source_sha256'],'checks':obj['checks'],'behavior_observed':passed,
          'learner_improvement_verified':False,'semantic_source_entailment_verified':False})
    num=sum(Fraction(u['credit']) for u in units);den=len(units)
    return {'units':units,'score_exact':str(num/den),'earned_weight':str(num),'total_weight':str(den),
            'outcome':'PASS' if num==den else 'FAIL','objectives':objective_reports}
