"""Exact finite-sample metrics. Nearest-rank percentiles are not confidence bounds."""
from fractions import Fraction
from ..release_v2.contracts import ContractError, integer

def percentile(values, numerator=95, denominator=100):
    if type(values) not in (tuple,list) or not values:raise ContractError('PERF_EMPTY_METRIC')
    for x in values:integer(x,'metric',0,2**63-1)
    integer(numerator,'percentile',1,denominator);integer(denominator,'denominator',1,10000)
    rank=(len(values)*numerator+denominator-1)//denominator
    return sorted(values)[rank-1]

def ratio(n,d):
    integer(n,'ratio_n',0,2**63-1);integer(d,'ratio_d',1,2**63-1)
    f=Fraction(n,d);return dict(numerator=f.numerator,denominator=f.denominator)

def concurrent_peak(intervals):
    events=[]
    for a,b in intervals:
        integer(a,'start',0,2**63-1);integer(b,'end',a+1,2**63-1)
        events.extend(((a,1),(b,-1)))
    active=peak=0
    for _,delta in sorted(events):active+=delta;peak=max(peak,active)
    return peak

def summarize(jobs,start_ns,end_ns,verified_successes):
    integer(start_ns,'start_ns',0,2**63-1);integer(end_ns,'end_ns',start_ns+1,2**63-1)
    if not jobs:raise ContractError('PERF_EMPTY_QUEUE')
    integer(verified_successes,'verified_successes',0,len(jobs))
    return dict(submitted=len(jobs),verified_successes=verified_successes,
        makespan_ns=end_ns-start_ns,
        p95_queue_ns=percentile([j['dispatch_ns']-j['enqueue_ns'] for j in jobs]),
        p95_latency_ns=percentile([j['complete_ns']-j['enqueue_ns'] for j in jobs]),
        p95_service_ns=percentile([j['complete_ns']-j['dispatch_ns'] for j in jobs]),
        peak_concurrency=concurrent_peak([(j['dispatch_ns'],j['complete_ns']) for j in jobs]),
        verified_jobs_per_second=ratio(verified_successes*1000000000,end_ns-start_ns))
