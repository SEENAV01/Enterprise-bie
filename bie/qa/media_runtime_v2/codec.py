"""Strict codecs. Operator policies and tool profiles are separate from candidate data."""
from dataclasses import fields as dc_fields,MISSING
from .common import *
from .storage import StreamArtifact
from .stream import StreamPolicy
from .motion import MotionPolicy,Track
from .native import NativeProfile,AVPolicy
from .speech import SpeechPolicy
from .game import NativeGamePolicy,ExtendedGamePolicy,StateConstraint

def obj(cls,value):
    require(type(value)is dict,'H5_CODEC_OBJECT')
    fs=dc_fields(cls);allowed={x.name for x in fs};required={x.name for x in fs if x.default is MISSING and x.default_factory is MISSING}
    require(required<=set(value)<=allowed,'H5_CODEC_FIELDS')
    return value.copy()
def rows(v):
    require(type(v)is list and len(v)<=4096,'H5_CODEC_ARRAY');return v

def load_policy(kind,data):
    v=strict_json(data)
    if kind=='stream':
        v=obj(StreamPolicy,v)
        for k in ('blank_windows','motion_windows'):
            if k in v:v[k]=tuple(tuple(rows(x)) for x in rows(v[k]))
        for k in ('allowed_cut_frames','sample_frames'):
            if k in v:v[k]=tuple(rows(v[k]))
        return StreamPolicy(**v)
    if kind=='motion':
        v=obj(MotionPolicy,v);v['required_meanings']=tuple(rows(v['required_meanings']));ts=[]
        for x in rows(v['tracks']):
            x=obj(Track,x);x['controls']=tuple(rows(x['controls']));ts.append(Track(**x))
        v['tracks']=tuple(ts);return MotionPolicy(**v)
    if kind=='av':
        v=obj(AVPolicy,v);v['required_evidence']=tuple(rows(v['required_evidence']));return AVPolicy(**v)
    if kind=='speech':
        v=obj(SpeechPolicy,v);ps=[]
        for pair in rows(v['pronunciation_forms']):
            require(type(pair)is list and len(pair)==2,'H5_CODEC_PRONUNCIATION');ps.append((pair[0],tuple(rows(pair[1]))))
        v['pronunciation_forms']=tuple(ps);return SpeechPolicy(**v)
    if kind=='native-game':
        v=obj(NativeGamePolicy,v);v['module_paths']=tuple(rows(v['module_paths']));return NativeGamePolicy(**v)
    if kind=='extended-game':
        v=obj(ExtendedGamePolicy,v);v['required_scenarios']=tuple(rows(v['required_scenarios']));v['required_mechanics']=tuple(tuple(rows(x)) for x in rows(v['required_mechanics']))
        v['state_ranges']=tuple(StateConstraint(**obj(StateConstraint,x)) for x in rows(v['state_ranges']))
        if 'conserved_groups' in v:
            groups=[]
            for x in rows(v['conserved_groups']):
                require(type(x)is list and len(x)==2,'H5_CODEC_CONSERVATION');groups.append((tuple(rows(x[0])),x[1]))
            v['conserved_groups']=tuple(groups)
        return ExtendedGamePolicy(**v)
    raise ContractError('H5_CODEC_KIND')

def load_native_profile(data):
    v=obj(NativeProfile,strict_json(data));v['files']=tuple(tuple(rows(x)) for x in rows(v['files']));v['python']=Tool(**obj(Tool,v['python']));return NativeProfile(**v)

def load_request(data,kind):
    v=strict_json(data);fields(v,('binding','artifact'),'H5_REQUEST_FIELDS')
    return Binding(**obj(Binding,v['binding'])),StreamArtifact(**obj(StreamArtifact,v['artifact']))
