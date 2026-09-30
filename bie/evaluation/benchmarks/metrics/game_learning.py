"""METRIC-014: paired, first-attempt item outcomes with retention and feedback.
Authored traces are not human learning evidence or a causal treatment estimate.
"""
from fractions import Fraction
from ..models import BenchmarkError,ident
from ..domains.structured import record,choice,probability,amount
from .common import ids,indexed,weight
from .delivery_common import integer,result_unit,unknown
PHASES=('pre','practice','post','delay')
def measure(reference,candidate,artifacts):
    record(reference,{'objectives','questions','minimum_delay_ms'})
    record(candidate,{'session_id','events'})
    ident(candidate['session_id']);delay=integer(reference['minimum_delay_ms'],0,7*86400000)
    goals=indexed(reference['objectives'],{'id','min_post_accuracy','min_delay_accuracy','min_gain','weight'},lower=1)
    questions=indexed(reference['questions'],{'id','objective_id','phase','options','correct_option','feedback_by_option'},lower=1)
    counts={k:{p:[] for p in PHASES} for k in goals}
    for g in goals.values():probability(g['min_post_accuracy']);probability(g['min_delay_accuracy']);amount(g['min_gain'],signed=True,maximum=1);weight(g)
    for k,q in questions.items():
        goal=ident(q['objective_id']);phase=choice(q['phase'],PHASES);opts=ids(q['options'],lower=2)
        if goal not in goals:raise BenchmarkError('UNKNOWN_REFERENCE_OBJECTIVE')
        if ident(q['correct_option']) not in opts:raise BenchmarkError('ANSWER_KEY_NOT_AN_OPTION')
        f=q['feedback_by_option']
        if type(f) is not dict or set(f)!=set(opts):raise BenchmarkError('REFERENCE_FEEDBACK_INCOMPLETE')
        for value in f.values():ident(value)
        counts[goal][phase].append(k)
    if any(not all(group.values()) for group in counts.values()):raise BenchmarkError('INCOMPLETE_PAIRED_REFERENCE_DESIGN')
    events=indexed(candidate['events'],{'id','question_id','option_id','feedback_id','time_ms'})
    seen={};prev=-1
    for e in events.values():
        qid=ident(e['question_id'])
        if qid not in questions:raise BenchmarkError('UNKNOWN_CANDIDATE_ITEM')
        if qid in seen:raise BenchmarkError('DUPLICATE_LEARNING_ATTEMPT')
        ident(e['option_id']);ident(e['feedback_id']);t=integer(e['time_ms'],0,30*86400000)
        if t<=prev:raise BenchmarkError('NONMONOTONIC_LEARNING_EVENTS')
        prev=t
        if e['option_id'] not in questions[qid]['options']:raise BenchmarkError('UNKNOWN_ANSWER_OPTION')
        seen[qid]=e
    units=[];statistics={}
    for key,g in sorted(goals.items()):
        why=[];acc={};times={p:[] for p in PHASES}
        for phase in PHASES:
            roster=counts[key][phase];correct=0
            for qid in roster:
                if qid not in seen:why.append('REQUIRED_LEARNING_EVENT_MISSING');continue
                e=seen[qid];q=questions[qid];times[phase].append(e['time_ms'])
                correct += e['option_id']==q['correct_option']
                if e['feedback_id']!=q['feedback_by_option'][e['option_id']]:why.append('MISCONCEPTION_FEEDBACK_MISMATCH')
            acc[phase]=Fraction(correct,len(roster))
        if acc['post']<probability(g['min_post_accuracy']):why.append('POST_ASSESSMENT_FLOOR_NOT_MET')
        if acc['delay']<probability(g['min_delay_accuracy']):why.append('RETENTION_FLOOR_NOT_MET')
        gain=acc['post']-acc['pre']
        if gain<amount(g['min_gain'],signed=True,maximum=1):why.append('PAIRED_GAIN_FLOOR_NOT_MET')
        for a,b in zip(PHASES,PHASES[1:]):
            if times[a] and times[b] and max(times[a])>=min(times[b]):why.append('LEARNING_PHASE_ORDER_VIOLATION')
        if times['post'] and times['delay'] and min(times['delay'])-max(times['post'])<delay:why.append('RETENTION_DELAY_TOO_SHORT')
        statistics[key]={**{p+'_accuracy_exact':str(acc[p]) for p in PHASES},'paired_gain_exact':str(gain)}
        units.append(result_unit(key,why,weight(g)))
    return units,[],{'assessment_scope':'CURATED_SINGLE_SESSION_FIRST_ATTEMPT_TRACES','statistics':statistics,
                     'human_learners_observed':False,'causal_learning_effect_estimated':False,'playable_game_verified':False}
