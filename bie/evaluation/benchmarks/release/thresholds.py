"""REL-001: pinned enterprise weighted threshold with a fixed metric denominator."""
from fractions import Fraction
from ..models import BenchmarkError,exact_fields,ident,version_tuple
from ..domains.structured import amount,choice
from .contracts import keyed_rows,score,pinned,gate_result

def normalize_scores(roster,rows):
    actual=keyed_rows(rows,{'id','status','score'},lower=0)
    if set(actual)-set(roster):raise BenchmarkError('UNEXPECTED_SCORE_ROW')
    values={};measured=set()
    for key in roster:
        if key not in actual:values[key]=Fraction(0);continue
        row=actual[key];choice(row['status'],{'MEASURED','BLOCKED','MISSING'});q=score(row['score'])
        if row['status']=='MEASURED':values[key]=q;measured.add(key)
        else:values[key]=Fraction(0)
    return values,measured

def evaluate(policy,rows,*,expected_policy_sha256):
    pinned(policy,expected_policy_sha256)
    exact_fields(policy,{'id','version','minimum_score','minimum_measured_fraction','metrics'})
    ident(policy['id']);version_tuple(policy['version'])
    floor=score(policy['minimum_score']);coverage_floor=score(policy['minimum_measured_fraction'])
    roster=keyed_rows(policy['metrics'],{'id','weight'},lower=1)
    weights={k:amount(r['weight'],positive=True,maximum=1000000) for k,r in roster.items()}
    values,measured=normalize_scores(roster,rows)
    den=sum(weights.values());value=sum(weights[k]*values[k] for k in roster)/den
    coverage=Fraction(len(measured),len(roster));reasons=[]
    if value<floor:reasons.append('ENTERPRISE_SCORE_BELOW_THRESHOLD')
    if coverage<coverage_floor:reasons.append('ENTERPRISE_COVERAGE_BELOW_THRESHOLD')
    return gate_result('ENTERPRISE_THRESHOLD',reasons,score_exact=str(value),minimum_score=str(floor),
        measured_fraction=str(coverage),expected_metric_count=len(roster),measured_metric_count=len(measured),
        missing_or_blocked=sorted(set(roster)-measured),policy_sha256=expected_policy_sha256)
