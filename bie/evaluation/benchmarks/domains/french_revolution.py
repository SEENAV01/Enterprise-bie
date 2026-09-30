"""HIST-001: bounded source-referenced 1789 event/date and claim typing pack.

Event data are a declared four-event reference profile, not a complete history.
Interpretations/motives are never silently converted into settled factual dates.
"""
from __future__ import annotations
from ..models import BenchmarkError, ident
from .structured import choice, record, sequence, unique_ids
from .temporal import date_interval, relation

EVENTS = {
    'estates_general_opening': {'date':'1789-05-05','place':'Versailles','source_ref':'versailles-estates-1789'},
    'tennis_court_oath': {'date':'1789-06-20','place':'Versailles','source_ref':'versailles-oath-1789'},
    'declaration_1789_text': {'date':'1789-08-26','source_ref':'elysee-declaration-1789'},
    'royal_departure_versailles': {'date':'1789-10-06','place':'Versailles','source_ref':'versailles-departure-1789'},
}
# Abstract proposition codes avoid rewarding string overlap in generated prose.
CLAIMS = {
    'estates_opening_date': ('FACT', 'versailles-estates-1789'),
    'oath_date': ('FACT', 'versailles-oath-1789'),
    'declaration_text_date': ('FACT', 'elysee-declaration-1789'),
    'declaration_article1_equal_rights_principle': ('TEXTUAL_PRINCIPLE', 'elysee-declaration-1789'),
    'declaration_article16_separation_powers': ('TEXTUAL_PRINCIPLE', 'elysee-declaration-1789'),
    'financial_crisis_contributed_to_convocation': ('ATTRIBUTED_INTERPRETATION', 'versailles-estates-1789'),
}


def solve(data: dict) -> dict:
    if type(data) is not dict:raise BenchmarkError('INVALID_FIELDS')
    op=data.get('op')
    if op=='event_facts':
        record(data, {'op','event_ids'})
        ids=unique_ids(data['event_ids'],upper=4)
        if any(key not in EVENTS for key in ids):raise BenchmarkError('EVENT_OUTSIDE_REFERENCE_PROFILE')
        return {'events':[{'event_id':key,**EVENTS[key]} for key in sorted(ids,key=lambda x:EVENTS[x]['date'])],
                'profile':'FOUR_REFERENCED_1789_EVENTS_NOT_COMPLETE_HISTORY'}
    if op=='audit_timeline':
        record(data, {'op','entries','required_event_ids'})
        required=unique_ids(data['required_event_ids'],upper=4)
        if any(key not in EVENTS for key in required):raise BenchmarkError('EVENT_OUTSIDE_REFERENCE_PROFILE')
        entries=sequence(data['entries'],lower=0,upper=4);seen=set();defects=[]
        for entry in entries:
            record(entry, {'event_id','date','source_ref'})
            key=ident(entry['event_id']);ident(entry['source_ref'])
            if key in seen:raise BenchmarkError('DUPLICATE_EVENT')
            seen.add(key)
            if key not in required:raise BenchmarkError('UNEXPECTED_EVENT')
            a=date_interval(entry['date'])
            y,m,d=map(int,EVENTS[key]['date'].split('-'))
            actual={'year':y,'era':'CE','month':m,'day':d,'precision':'day','calendar':'proleptic_gregorian'}
            expected=date_interval(actual)
            if a!=expected:
                defects.append({'event_id':key,'reason':'DATE_MISMATCH_OR_INSUFFICIENT_PRECISION'})
            if entry['source_ref']!=EVENTS[key]['source_ref']:
                defects.append({'event_id':key,'reason':'SOURCE_EVENT_MISMATCH'})
        defects += [{'event_id':key,'reason':'MISSING_EVENT'} for key in sorted(set(required)-seen)]
        return {'consistent':not defects,'defects':sorted(defects,key=lambda x:(x['event_id'],x['reason'])),
                'references_are_links_not_captured_passages':True}
    if op=='classify_claim':
        record(data, {'op','claim_id','source_ref'})
        key=choice(data['claim_id'],CLAIMS)
        category,source=CLAIMS[key]
        if data['source_ref']!=source:raise BenchmarkError('CLAIM_SOURCE_MISMATCH')
        return {'claim_type':category,'source_ref':source,
                'historical_practice_established_by_normative_text':False,
                'profile':'DECLARED_SOURCE_LINKED_CLAIM_TYPE_NOT_ENTAILMENT'}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
