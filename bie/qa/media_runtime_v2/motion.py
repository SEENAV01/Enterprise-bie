"""HARD018: full-frame state audit and exact cubic Bernstein range screening.

Full discrete coverage is not subframe capture. A bounded Bernstein enclosure
can establish a scalar cubic bound over all t in [0,1]; unresolved enclosures
remain review-required. Springs/3D/camera composition are not silently linearized.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from fractions import Fraction
import hashlib
from .common import *
from .storage import snapshot,StreamArtifact
from ...animation_intelligence.qa_contracts import Event
from ...animation_intelligence.temporal_conflict_qa import evaluate as native_temporal


def bezier_value(controls,t):
    require(len(controls)==4,'H5_CUBIC_CONTROLS');t=q(qt(t)) if type(t) is Fraction else q(t);require(0<=t<=1,'H5_CUBIC_TIME')
    row=[q(v) for v in controls]
    while len(row)>1:row=[(1-t)*a+t*b for a,b in zip(row,row[1:])]
    return row[0]


def enclose_cubic(controls,lo,hi,*,depth=12):
    """Return CLEAR, VIOLATION or UNRESOLVED with no sampling-as-proof shortcut."""
    require(type(controls)in(tuple,list) and len(controls)==4,'H5_CUBIC_CONTROLS')
    row=tuple(q(v) for v in controls);lo=q(lo);hi=q(hi);require(lo<=hi,'H5_RANGE')
    integer(depth,'depth',0,16)
    def check(c,n):
        if c[0]<lo or c[0]>hi or c[-1]<lo or c[-1]>hi:return 'VIOLATION'
        if min(c)>=lo and max(c)<=hi:return 'CLEAR'
        if n==0:return 'UNRESOLVED'
        a=(c[0]+c[1])/2;b=(c[1]+c[2])/2;d=(c[2]+c[3])/2
        e=(a+b)/2;f=(b+d)/2;g=(e+f)/2
        left=check((c[0],a,e,g),n-1);right=check((g,f,d,c[3]),n-1)
        return 'VIOLATION' if 'VIOLATION' in (left,right) else 'UNRESOLVED' if 'UNRESOLVED' in (left,right) else 'CLEAR'
    return check(row,depth)


@dataclass(frozen=True)
class Track:
    object_id:str
    property:str
    controls:tuple[str,str,str,str]
    minimum:str
    maximum:str
    max_speed:str
    def __post_init__(self):
        token(self.object_id,'object');require(self.property in ('x','y','opacity','scale','angle'),'H5_TRACK_PROPERTY')
        require(type(self.controls)is tuple and len(self.controls)==4,'H5_TRACK_CONTROLS')
        for v in self.controls:q(v)
        require(q(self.minimum)<=q(self.maximum) and q(self.max_speed)>0,'H5_TRACK_RANGE')


@dataclass(frozen=True)
class MotionPolicy:
    frames:int
    fps:str
    tracks:tuple[Track,...]
    required_meanings:tuple[str,...]
    mode:str='standard'
    tolerance:str='0'
    reduced_speed_factor:str='1/2'
    max_trace_bytes:int=128*1024**2
    def __post_init__(self):
        integer(self.frames,'frames',2,216000);require(1<=q(self.fps)<=240,'H5_FPS')
        require(type(self.tracks)is tuple and 1<=len(self.tracks)<=64 and all(type(t)is Track for t in self.tracks),'H5_TRACKS')
        require(len({(t.object_id,t.property) for t in self.tracks})==len(self.tracks),'H5_TRACK_DUPLICATE')
        checked_ids(self.required_meanings,'MEANINGS');require(self.mode in ('standard','reduced'),'H5_MOTION_MODE')
        require(q(self.tolerance)>=0 and 0<q(self.reduced_speed_factor)<=1,'H5_MOTION_TOLERANCE')
        integer(self.max_trace_bytes,'trace_limit',1,1024**3)


def native_event_check(events):
    require(type(events)is tuple and events and all(type(e)is Event for e in events),'H5_NATIVE_ANIMATION_EVENTS')
    # Exercise original native QA, but never elevate its score/status to release.
    return native_temporal(events)


def inspect_motion(root,trace:StreamArtifact,binding,policy,*,native_events=()):
    policy_binding(binding,policy);findings=[];notes=[];previous=None;count=0;h=hashlib.sha256()
    duration=Fraction(policy.frames-1,1)/q(policy.fps)
    for t in policy.tracks:
        state=enclose_cubic(t.controls,t.minimum,t.maximum)
        if state=='VIOLATION':fail(findings,'H5_CONTINUOUS_RANGE_VIOLATION',t.object_id+'.'+t.property)
        elif state=='UNRESOLVED':findings.append(Finding('H5_CONTINUOUS_RANGE_UNRESOLVED',t.object_id+'.'+t.property))
        derivative=tuple(3*(q(b)-q(a))/duration for a,b in zip(t.controls,t.controls[1:]))
        speed=q(t.max_speed)*(q(policy.reduced_speed_factor) if policy.mode=='reduced' else 1)
        # Derivative is quadratic Bernstein. Bound by its control hull; conservative
        # uncertainty is not converted to a proven violation or a pass.
        if max(abs(x) for x in derivative)>speed:findings.append(Finding('H5_CONTINUOUS_SPEED_REVIEW',t.object_id+'.'+t.property))
    if native_events:
        native=native_event_check(native_events)
        if native.status=='BLOCKED':fail(findings,'H5_NATIVE_TEMPORAL_CONFLICT')
        notes.append({'native_qa_id':native.qa_id,'native_status':native.status,'accepted':False})
    with snapshot(root,trace,maximum=policy.max_trace_bytes) as (path,byte_manifest):
        with path.open('rb') as f:
            while line:=f.readline(65537):
                require(len(line)<=65536 and line.endswith(b'\n'),'H5_STATE_LINE_BUDGET')
                r=strict_json(line);fields(r,('frame','timestamp','mode','meaning_ids','values','binding'),'H5_STATE_FIELDS')
                require(type(r['frame'])is int and r['frame']==count,'H5_STATE_FRAME_COVERAGE')
                require(count<policy.frames,'H5_STATE_EXTRA_FRAME');binding_matches(r['binding'],binding)
                require(q(r['timestamp'])==Fraction(count,1)/q(policy.fps),'H5_STATE_CLOCK')
                require(r['mode']==policy.mode,'H5_STATE_MODE')
                checked_ids(r['meaning_ids'],'STATE_MEANINGS')
                if set(r['meaning_ids'])!=set(policy.required_meanings):fail(findings,'H5_REDUCED_MEANING_LOSS',str(count))
                require(type(r['values'])is dict,'H5_STATE_VALUES')
                expected_keys={t.object_id+'.'+t.property for t in policy.tracks}
                require(set(r['values'])==expected_keys,'H5_STATE_OBJECT_INVENTORY')
                for t in policy.tracks:
                    key=t.object_id+'.'+t.property;value=q(r['values'][key]);target=bezier_value(t.controls,Fraction(count,policy.frames-1))
                    if abs(value-target)>q(policy.tolerance):fail(findings,'H5_STATE_TRAJECTORY_MISMATCH',str(count)+':'+key)
                    if value<q(t.minimum) or value>q(t.maximum):fail(findings,'H5_STATE_RANGE',str(count)+':'+key)
                    if previous is not None:
                        speed=abs(value-q(previous[key]))*q(policy.fps)
                        maximum=q(t.max_speed)*(q(policy.reduced_speed_factor) if policy.mode=='reduced' else 1)
                        if speed>maximum:fail(findings,'H5_STATE_SPEED',str(count)+':'+key)
                previous=r['values'];h.update(line);count+=1
                require(len(findings)<8192,'H5_MOTION_FINDING_BUDGET')
    require(count==policy.frames,'H5_STATE_MISSING_FRAME')
    return findings_report('BIE-QA-HARD-018',binding,findings,{'frames':count,'trace':asdict(trace),
        'trace_bytes':byte_manifest,'state_chain_sha256':h.hexdigest(),'native':notes,
        'discrete_full_coverage':True,'continuous_scalar_model':'cubic Bernstein only',
        'runtime_trace_authentication_required':True,'live_playback_proven':False})
