"""HIST-003: BCE/CE, partial precision and definite-before partial orders."""
from __future__ import annotations
from ..models import BenchmarkError, ident
from .structured import record, sequence
from .temporal import astronomical_year, date_interval, relation


def solve(data: dict) -> dict:
    if type(data) is not dict:raise BenchmarkError('INVALID_FIELDS')
    op=data.get('op')
    if op=='compare_dates':
        record(data, {'op','a','b'})
        a,b=date_interval(data['a']),date_interval(data['b'])
        return {'relation':relation(a,b),
                'b_minus_a_days_min':b[0]-a[1],
                'b_minus_a_days_max':b[1]-a[0],
                'profile':'PROLEPTIC_GREGORIAN_INTERVAL_ARITHMETIC_NOT_CAUSALITY'}
    if op=='year_difference':
        record(data, {'op','a_year','a_era','b_year','b_era'})
        a=astronomical_year(data['a_year'],data['a_era'])
        b=astronomical_year(data['b_year'],data['b_era'])
        return {'signed_year_number_difference':b-a,
                'profile':'YEAR_LABEL_DIFFERENCE_NOT_PRECISE_ELAPSED_DURATION'}
    if op=='partial_order':
        record(data, {'op','events'})
        events={}
        for event in sequence(data['events'],upper=32):
            record(event, {'id','date'})
            key=ident(event['id'])
            if key in events:raise BenchmarkError('DUPLICATE_EVENT')
            events[key]=date_interval(event['date'])
        before=sorted((a,b) for a in events for b in events if a!=b and relation(events[a],events[b])=='BEFORE')
        unresolved=sorted((a,b) for a in events for b in events if a<b and relation(events[a],events[b])=='OVERLAPPING_OR_UNCERTAIN')
        same=sorted((a,b) for a in events for b in events if a<b and relation(events[a],events[b])=='SAME_DAY')
        return {'definitely_before':[list(p) for p in before],
                'overlapping_or_uncertain':[list(p) for p in unresolved],
                'same_day':[list(p) for p in same],
                'unique_total_order':not unresolved and not same,
                'profile':'PRECISION_PRESERVING_PARTIAL_ORDER'}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
