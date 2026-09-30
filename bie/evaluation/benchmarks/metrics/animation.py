"""METRIC-010: complete sampled trajectories and finite-difference bounds.
Unobserved inter-sample motion is explicitly outside this profile.
"""
from fractions import Fraction
from ..models import BenchmarkError,ident
from ..domains.structured import record,sequence,amount
from .common import indexed,weight
from .delivery_common import integer,unknown,result_unit

def samples(rows,duration):
    out=[]
    for row in sequence(rows,lower=2,upper=256):
        record(row,{'frame','value'});f=integer(row['frame'],0,duration-1);v=amount(row['value'],signed=True)
        if out and f<=out[-1][0]: raise BenchmarkError('NONINCREASING_SAMPLE_FRAME')
        out.append((f,v))
    return out

def interpolate(knots,frame):
    for (f,a),(g,b) in zip(knots,knots[1:]):
        if f<=frame<=g:return a+(b-a)*Fraction(frame-f,g-f)
    raise BenchmarkError('REFERENCE_KNOT_COVERAGE_MISSING')

def measure(reference,candidate,artifacts):
    record(reference,{'frame_count','fps','sample_frames','tracks'})
    record(candidate,{'tracks'})
    n=integer(reference['frame_count'],2,100000);fps=integer(reference['fps'],1,120)
    frames=[integer(x,0,n-1) for x in sequence(reference['sample_frames'],lower=2,upper=256)]
    if sorted(set(frames))!=frames or frames[0]!=0 or frames[-1]!=n-1: raise BenchmarkError('INVALID_REFERENCE_SAMPLE_ROSTER')
    refs=indexed(reference['tracks'],{'id','property','unit','knots','absolute_tolerance','minimum','maximum','max_speed','max_acceleration','weight'},lower=1)
    acts=indexed(candidate['tracks'],{'id','property','unit','samples'});unknown(acts,refs)
    units=[]
    for k,r in sorted(refs.items()):
        ident(r['property']);ident(r['unit']);weight(r);knots=samples(r['knots'],n)
        if knots[0][0]!=0 or knots[-1][0]!=n-1:raise BenchmarkError('REFERENCE_KNOT_COVERAGE_MISSING')
        tol=amount(r['absolute_tolerance'],maximum=1000);low=amount(r['minimum'],signed=True);high=amount(r['maximum'],signed=True)
        speed=amount(r['max_speed']);accel=amount(r['max_acceleration'])
        if low>high or any(not low<=v<=high for f,v in knots):raise BenchmarkError('REFERENCE_TRAJECTORY_OUT_OF_BOUNDS')
        # Validate the trusted reference itself before judging any candidate.
        # Check knot slopes as well as finite differences on the required roster.
        for reference_samples in (knots,[(f,interpolate(knots,f)) for f in frames]):
            rs=[(Fraction(g-f,fps),(b-a)*fps/(g-f)) for (f,a),(g,b) in zip(reference_samples,reference_samples[1:])]
            if any(abs(v)>speed for dt,v in rs) or any(abs((v2-v1)/((dt1+dt2)/2))>accel for (dt1,v1),(dt2,v2) in zip(rs,rs[1:])):
                raise BenchmarkError('REFERENCE_DYNAMICS_OUT_OF_BOUNDS')
        reasons=[]
        if k not in acts: reasons.append('REQUIRED_ANIMATION_TRACK_MISSING')
        else:
            a=acts[k];ident(a['property']);ident(a['unit']);ss=samples(a['samples'],n)
            if (a['property'],a['unit'])!=(r['property'],r['unit']):reasons.append('PROPERTY_OR_UNIT_MISMATCH')
            if [f for f,v in ss]!=frames: reasons.append('ANIMATION_SAMPLE_ROSTER_MISMATCH')
            if any(abs(v-interpolate(knots,f))>tol for f,v in ss): reasons.append('TRAJECTORY_FIDELITY_ERROR')
            if any(not low<=v<=high for f,v in ss): reasons.append('ANIMATION_VALUE_OUT_OF_BOUNDS')
            speeds=[((g-f)/Fraction(fps), (b-a)*fps/(g-f)) for (f,a),(g,b) in zip(ss,ss[1:])]
            if any(abs(v)>speed for dt,v in speeds): reasons.append('SPEED_BOUND_EXCEEDED')
            if any(abs((v2-v1)/((dt1+dt2)/2))>accel for (dt1,v1),(dt2,v2) in zip(speeds,speeds[1:])): reasons.append('ACCELERATION_BOUND_EXCEEDED')
        units.append(result_unit(k,reasons,weight(r)))
    return units,[],{'assessment_scope':'DECLARED_SAMPLE_TIMES_AND_TRAJECTORIES','continuous_motion_proven':False}
