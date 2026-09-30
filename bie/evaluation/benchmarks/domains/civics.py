"""CIV-001: selected descriptive UK institution roles, not political evaluation.

Profile pinned to consulted official introductory pages on 2026-09-29.
The ordinary two-house bill model excludes special legislative routes. It never
rates parties, officials, choices or policies; it checks educational assertions.
"""
from __future__ import annotations
from ..models import BenchmarkError, ident
from .structured import choice, observed_claims, record, sequence
PROFILE='UK_INTRO_2026-09-29'
ROLES={'government_and_parliament_identical':False,
       'day_to_day_public_administration':'government',
       'scrutinises_government':'parliament',
       'ministers_can_also_sit_in_parliament':True,
       'bill_is_already_an_act':False}

def solve(data: dict) -> dict:
    if type(data) is not dict:raise BenchmarkError('INVALID_FIELDS')
    op=data.get('op')
    if op=='audit_roles':
        record(data, {'op','profile','claims'});choice(data['profile'],{PROFILE})
        return {**observed_claims(data['claims'],ROLES),'jurisdiction':'UK','reference_profile':PROFILE}
    if op=='ordinary_bill_trace':
        record(data, {'op','profile','route','events'})
        choice(data['profile'],{PROFILE});choice(data['route'],{'ordinary_two_house_bill'})
        events=sequence(data['events'],lower=1,upper=4)
        allowed={'introduced','commons_agreed','lords_agreed','royal_assent'}
        steps=[choice(x,allowed) for x in events]
        if len(set(steps))!=len(steps):raise BenchmarkError('DUPLICATE_EVENT')
        defects=[];seen=set()
        for step in steps:
            if step!='introduced' and 'introduced' not in seen:defects.append({'event':step,'reason':'INTRODUCTION_MISSING_BEFORE_EVENT'})
            if step=='royal_assent' and not {'commons_agreed','lords_agreed'}<=seen:
                defects.append({'event':step,'reason':'BOTH_HOUSES_AGREEMENT_REQUIRED_IN_PROFILE'})
            if 'royal_assent' in seen:defects.append({'event':step,'reason':'EVENT_AFTER_ASSENT'})
            seen.add(step)
        return {'trace_consistent':not defects,'act_in_this_profile':not defects and 'royal_assent' in seen,
                'defects':defects,'profile':'ORDINARY_TWO_HOUSE_BILL_NOT_EXCEPTIONS'}
    if op=='fictional_competence':
        # Explicitly fictional constitutional scenario supplied in the benchmark
        # question, not a current-country legal or normative assessment.
        record(data, {'op','jurisdiction','institutions','request'})
        choice(data['jurisdiction'],{'FICTIONAL_EDUCATIONAL_SCENARIO'})
        powers={}
        for row in sequence(data['institutions']):
            record(row, {'id','powers'});key=ident(row['id'])
            if key in powers:raise BenchmarkError('DUPLICATE_ID')
            p=[ident(v) for v in sequence(row['powers'])]
            if len(set(p))!=len(p):raise BenchmarkError('DUPLICATE_POWER')
            powers[key]=set(p)
        record(data['request'], {'institution','power'})
        who=ident(data['request']['institution']);what=ident(data['request']['power'])
        if who not in powers:raise BenchmarkError('UNKNOWN_INSTITUTION')
        return {'assigned_in_supplied_scenario':what in powers[who],
                'jurisdiction':'FICTIONAL_EDUCATIONAL_SCENARIO','policy_merit_evaluated':False}
    raise BenchmarkError('UNSUPPORTED_OPERATION')
