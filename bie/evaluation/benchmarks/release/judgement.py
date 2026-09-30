"""Pinned, weighted rubric units for human/model structured judgements."""
from fractions import Fraction
from ..models import BenchmarkError,digest,exact_fields,ident,text,version_tuple
from ..domains.structured import amount,unique_ids,sequence
from .contracts import keyed_rows,score

def rubric(value):
    exact_fields(value,{'id','version','owner_id','units'})
    ident(value['id']);version_tuple(value['version']);ident(value['owner_id'])
    rows=keyed_rows(value['units'],{'id','weight','criterion','evidence_ids'},lower=1,upper=128)
    for r in rows.values():
        amount(r['weight'],positive=True,maximum=1000000);text(r['criterion'],4000);unique_ids(r['evidence_ids'],lower=1,upper=128)
    return rows

def grade(value,units):
    refs=rubric(value)
    rows=keyed_rows(units,{'id','credit','rationale','evidence_ids'},lower=0,upper=128)
    if set(refs)!=set(rows):raise BenchmarkError('INCOMPLETE_JUDGEMENT_ROSTER')
    numerator=Fraction(0);denominator=Fraction(0);reasons=[]
    for key,r in sorted(refs.items()):
        u=rows[key];credit=score(u['credit']);text(u['rationale'],4000)
        evidence=unique_ids(u['evidence_ids'],lower=1,upper=128)
        if set(evidence)-set(r['evidence_ids']):raise BenchmarkError('UNKNOWN_JUDGEMENT_EVIDENCE')
        w=amount(r['weight'],positive=True,maximum=1000000);denominator+=w;numerator+=w*credit
        if credit<1:reasons.append('RUBRIC_UNIT_NOT_FULLY_SATISFIED')
    return numerator/denominator,reasons
