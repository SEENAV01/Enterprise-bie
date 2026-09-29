"""Exact scalar trajectories; no sampling-as-proof or floating point time budgets."""
from fractions import Fraction
from ..release_v2.contracts import ContractError, integer
from .models import Track,FrameRate

SUPPORTED=('linear','step_end')

def frame_time_ms(frame_index:int,fps:FrameRate)->Fraction:
    integer(frame_index,'frame_index',0,20_736_000)
    if type(fps) is not FrameRate:raise ContractError('ANI_FPS_TYPE')
    return Fraction(frame_index*1000*fps.denominator,fps.numerator)

def value_at(track:Track,time_ms,*,side='right')->Fraction:
    if type(track) is not Track or track.interpolation not in SUPPORTED:raise ContractError('ANI_UNSUPPORTED_INTERPOLATION')
    if type(time_ms) not in (int,Fraction) or side not in ('left','right'):raise ContractError('ANI_TIME_OR_SIDE_TYPE')
    t=Fraction(time_ms)
    if not track.start_ms<=t<=track.end_ms:raise ContractError('ANI_TIME_OUTSIDE_TRACK')
    if t==track.start_ms:return Fraction(track.keyframes[0].value)
    for a,b in zip(track.keyframes,track.keyframes[1:]):
        if a.time_ms<t<=b.time_ms:
            if track.interpolation=='step_end':return Fraction(b.value if t==b.time_ms and side=='right' else a.value)
            return a.value+Fraction((b.value-a.value)*(t-a.time_ms),b.time_ms-a.time_ms)
    raise ContractError('ANI_TRAJECTORY_UNDEFINED')

def segments(track):
    """Intervals are half-open; step_end jumps occur at the right boundary."""
    if track.interpolation not in SUPPORTED:raise ContractError('ANI_UNSUPPORTED_INTERPOLATION')
    return tuple((a.time_ms,b.time_ms,Fraction((b.value-a.value)*1000,b.time_ms-a.time_ms) if track.interpolation=='linear' else Fraction(0))
                 for a,b in zip(track.keyframes,track.keyframes[1:]))

def reversal_count(values):
    signs=[1 if b>a else -1 for a,b in zip(values,values[1:]) if a!=b]
    return sum(a!=b for a,b in zip(signs,signs[1:]))

def violates_timing(rule,left,right):
    a,b=left.start_ms,left.end_ms;c,d=right.start_ms,right.end_ms;t=rule.tolerance_ms
    return {'before':b>c+t,'after':a<d-t,'start_sync':abs(a-c)>t,'end_sync':abs(b-d)>t,
            'covers':a>c+t or b<d-t,'overlaps':min(b,d)-max(a,c)<rule.minimum_overlap_ms}[rule.relation]

def invariant_counterexample(rule,tracks):
    """For linear/step tracks, extrema of linear constraints occur at knots/sides."""
    ts=[tracks[i] for i in rule.track_ids]
    if any(t.interpolation not in SUPPORTED for t in ts):raise ContractError('ANI_UNSUPPORTED_INTERPOLATION')
    if any(t.start_ms>rule.start_ms or t.end_ms<rule.end_ms for t in ts):raise ContractError('ANI_INVARIANT_COVERAGE')
    points=sorted({rule.start_ms,rule.end_ms}|{k.time_ms for t in ts for k in t.keyframes if rule.start_ms<=k.time_ms<=rule.end_ms})
    for time in points:
        # The left limit at the START lies outside this closed proof window.
        for side in ('right',) if time==rule.start_ms else ('left','right'):
            vals=[value_at(t,time,side=side) for t in ts]
            bad=(abs(sum(vals)-rule.value)>rule.tolerance if rule.kind=='sum_constant' else
                 any(a>b+rule.tolerance for a,b in zip(vals,vals[1:])) if rule.kind=='ordered' else
                 any(abs(v-vals[0])>rule.tolerance for v in vals[1:]))
            if bad:return dict(time_ms=time,side=side,values=[str(v) for v in vals])
    return None

def trajectory_motion(request,policy):
    """Per-interval peaks, vector speeds, jumps and reversals. All thresholds external."""
    violations=[];stats=dict(peak_objects=0,peak_sum_rate_ppm=Fraction(0),peak_speed_squared=Fraction(0),max_reversals=0)
    limits=policy.limits
    for mode in policy.modes:
        tracks=[t for t in request.tracks if t.mode_id==mode.mode_id and t.interpolation in SUPPORTED]
        rates=[(t,a,b,v) for t in tracks for a,b,v in segments(t)]
        points=sorted({x for _,a,b,_ in rates for x in (a,b)})
        span=max(mode.width_px,mode.height_px)*1000
        speed=limits.reduced_max_speed_mpx_per_second if mode.kind=='reduced' else limits.max_speed_mpx_per_second
        rotation=limits.reduced_max_rotation_mdeg_per_second if mode.kind=='reduced' else limits.max_rotation_mdeg_per_second
        scale=limits.reduced_max_scale_ppm_per_second if mode.kind=='reduced' else limits.max_scale_ppm_per_second
        jump_limit=limits.reduced_max_jump_ppm if mode.kind=='reduced' else limits.max_jump_ppm
        for a,b in zip(points,points[1:]):
            channels={};active=set();total=Fraction(0)
            for t,s,e,v in rates:
                if s<=a<e and v and t.property!='value_milli':
                    channels.setdefault(t.object_id,{}).setdefault(t.property,[]).append(v);active.add(t.object_id)
                    norm=span if t.property in ('x_mpx','y_mpx') else 360000 if t.property=='rotation_mdeg' else 1000000
                    total+=abs(v)*1000000/norm
            stats['peak_objects']=max(stats['peak_objects'],len(active));stats['peak_sum_rate_ppm']=max(stats['peak_sum_rate_ppm'],total)
            if len(active)>limits.max_simultaneous_objects:violations.append(('ANI_EXCESSIVE_CONCURRENCY',mode.mode_id,a))
            if total>limits.max_sum_normalized_rate_ppm:violations.append(('ANI_PEAK_MOTION_BUDGET',mode.mode_id,a))
            for oid,ch in channels.items():
                # Conflicting writers are rejected separately; conservative component magnitudes here.
                x=sum(abs(v) for v in ch.get('x_mpx',()));y=sum(abs(v) for v in ch.get('y_mpx',()))
                s2=x*x+y*y;stats['peak_speed_squared']=max(stats['peak_speed_squared'],s2)
                if s2>speed*speed:violations.append(('ANI_SPEED_LIMIT',oid,a))
                for prop,limit in [('rotation_mdeg',rotation),('scale_ppm',scale),('opacity_ppm',limits.max_opacity_ppm_per_second),('progress_ppm',limits.max_progress_ppm_per_second)]:
                    if sum(abs(v) for v in ch.get(prop,()))>limit:violations.append(('ANI_PROPERTY_RATE_LIMIT',oid+':'+prop,a))
        grouped={}
        jumps={}
        for t in tracks:grouped.setdefault((t.object_id,t.property),[]).append(t)
        for (oid,prop),ts in sorted(grouped.items()):
            ts.sort(key=lambda t:(t.start_ms,t.track_id));vals=[]
            for i,t in enumerate(ts):
                if i and ts[i-1].end_ms<=t.start_ms and ts[i-1].keyframes[-1].value!=t.keyframes[0].value:
                    violations.append(('ANI_UNDECLARED_PROPERTY_JUMP',oid,t.start_ms))
                vals.extend(k.value for k in t.keyframes)
                if t.interpolation=='step_end' and prop!='value_milli':
                    norm=span if prop in ('x_mpx','y_mpx') else 360000 if prop=='rotation_mdeg' else 1000000
                    for a,b in zip(t.keyframes,t.keyframes[1:]):
                        magnitude=Fraction(abs(b.value-a.value)*1000000,norm)
                        if magnitude>jump_limit:violations.append(('ANI_STEP_JUMP_LIMIT',oid,b.time_ms))
                        if magnitude:jumps.setdefault(b.time_ms,[]).append((oid,magnitude))
            rev=reversal_count(vals);stats['max_reversals']=max(stats['max_reversals'],rev)
            if prop!='value_milli' and rev>limits.max_reversals:violations.append(('ANI_REVERSAL_LIMIT',oid,ts[0].start_ms))
        for time,js in jumps.items():
            # Count instantaneous jumps and simultaneous continuous movement together.
            moving={t.object_id for t,s,e,v in rates if s<=time<e and v and t.property!='value_milli'}
            count=len(moving|{oid for oid,_ in js});stats['peak_objects']=max(stats['peak_objects'],count)
            if count>limits.max_simultaneous_objects:violations.append(('ANI_EXCESSIVE_CONCURRENCY',mode.mode_id,time))
            if sum(v for _,v in js)>jump_limit:violations.append(('ANI_AGGREGATE_STEP_JUMP',mode.mode_id,time))
    return tuple(sorted(set(violations))),stats
