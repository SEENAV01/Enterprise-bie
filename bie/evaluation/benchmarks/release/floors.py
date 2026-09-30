"""REL-002: mandatory per-metric hard floors; averages cannot override failures."""
from ..models import exact_fields,ident
from .contracts import keyed_rows,score,pinned,gate_result
from .thresholds import normalize_scores

def evaluate(policy,rows,*,expected_policy_sha256):
    pinned(policy,expected_policy_sha256);exact_fields(policy,{'id','floors'});ident(policy['id'])
    refs=keyed_rows(policy['floors'],{'id','minimum'},lower=1)
    minimums={k:score(v['minimum']) for k,v in refs.items()}
    values,measured=normalize_scores(refs,rows);failures=[]
    for key in sorted(refs):
        if key not in measured:failures.append({'id':key,'reason':'CRITICAL_METRIC_NOT_MEASURED'})
        elif values[key]<minimums[key]:failures.append({'id':key,'reason':'CRITICAL_HARD_FLOOR_BREACHED'})
    return gate_result('CRITICAL_HARD_FLOORS',[x['reason'] for x in failures],failures=failures,
                       required_metric_count=len(refs),policy_sha256=expected_policy_sha256)
