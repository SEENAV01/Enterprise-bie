"""REL-003: domain minima, fixed case rosters and independent leakage groups."""
from fractions import Fraction
from ..models import BenchmarkError,exact_fields,ident
from ..domains.structured import amount
from .contracts import keyed_rows,score,pinned,gate_result,bounded_int
from .thresholds import normalize_scores

def evaluate(policy,roster,rows,*,expected_policy_sha256):
    pinned(policy,expected_policy_sha256);exact_fields(policy,{'id','domains'});ident(policy['id'])
    refs=keyed_rows(policy['domains'],{'id','minimum_score','minimum_cases','minimum_measured_fraction'},lower=1)
    cases=keyed_rows(roster,{'id','domain','leakage_group','weight'},lower=1)
    for case in cases.values():ident(case['domain']);ident(case['leakage_group']);amount(case['weight'],positive=True,maximum=1000000)
    if {r['domain'] for r in cases.values()}!=set(refs):raise BenchmarkError('DOMAIN_POLICY_ROSTER_MISMATCH')
    values,measured=normalize_scores(cases,rows);results=[];all_reasons=[]
    for key,p in sorted(refs.items()):
        floor=score(p['minimum_score']);minimum=bounded_int(p['minimum_cases'],1,1000)
        cover=score(p['minimum_measured_fraction']);ids=[k for k,r in cases.items() if r['domain']==key]
        den=sum(amount(cases[k]['weight'],positive=True) for k in ids)
        value=sum(amount(cases[k]['weight'],positive=True)*values[k] for k in ids)/den
        good=set(ids)&measured;coverage=Fraction(len(good),len(ids))
        groups={cases[k]['leakage_group'] for k in good};why=[]
        if len(groups)<minimum:why.append('DOMAIN_INDEPENDENT_CASE_MINIMUM_NOT_MET')
        if value<floor:why.append('DOMAIN_SCORE_BELOW_MINIMUM')
        if coverage<cover:why.append('DOMAIN_COVERAGE_BELOW_MINIMUM')
        all_reasons.extend(why);results.append({'id':key,'score_exact':str(value),'measured_fraction':str(coverage),
            'expected_cases':len(ids),'measured_cases':len(good),'independent_groups':len(groups),'reasons':why})
    return gate_result('DOMAIN_MINIMUMS',all_reasons,domains=results,policy_sha256=expected_policy_sha256)
