"""Closed, operator-controlled technical video QA contracts; no acceptance flags."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from fractions import Fraction
from ..release_v2.contracts import (ArtifactRef, ContractError, token, integer, sha256,
                                   revision, choice, digest, tuple_tokens)

VERSION='bie.qa.video/1'
MAX_FRAMES=24000

def records(value, cls, name, minimum=0, maximum=4096):
    if type(value) is not tuple or not minimum <= len(value) <= maximum or any(type(v) is not cls for v in value):
        raise ContractError('VIDEO_RECORDS',name)

def refs(value,name,minimum=0):
    records(value,ArtifactRef,name,minimum)
    if len({v.artifact_id for v in value})!=len(value) or len({v.path for v in value})!=len(value):
        raise ContractError('VIDEO_DUPLICATE_ARTIFACT',name)

def artifact_digest(value):
    refs(value,'artifacts');return digest([asdict(v) for v in sorted(value,key=lambda a:a.artifact_id)])

def boolean(v,name):
    if type(v) is not bool:raise ContractError('VIDEO_BOOL',name)

def nonblank(v,name,limit=4096):
    if type(v) is not str or not v.strip() or len(v)>limit or any(ord(c)<32 for c in v):raise ContractError('VIDEO_TEXT',name)

@dataclass(frozen=True,slots=True)
class Window:
    start:int
    end:int
    def __post_init__(self):
        integer(self.start,'window.start',0,MAX_FRAMES-1);integer(self.end,'window.end',self.start+1,MAX_FRAMES)
    def contains(self,frame):return self.start<=frame<self.end

@dataclass(frozen=True,slots=True)
class RegionExpectation:
    region_id:str
    frame:int
    x:int
    y:int
    width:int
    height:int
    reference:ArtifactRef
    max_error_ppm:int=20000
    def __post_init__(self):
        token(self.region_id,'region_id');integer(self.frame,'frame',0,MAX_FRAMES-1)
        integer(self.x,'x',-8192,8192);integer(self.y,'y',-8192,8192)
        integer(self.width,'width',1,8192);integer(self.height,'height',1,8192)
        if type(self.reference) is not ArtifactRef:raise ContractError('VIDEO_REGION_REFERENCE')
        integer(self.max_error_ppm,'region.max_error_ppm',0,1000000)

@dataclass(frozen=True,slots=True)
class VideoPolicy:
    composition_id:str
    expected_input_digest:str
    width:int
    height:int
    fps_numerator:int
    fps_denominator:int
    expected_frames:int
    require_audio:bool=False
    codecs:tuple[str,...]=('h264',)
    pixel_formats:tuple[str,...]=('yuv420p',)
    compile_tools:tuple[str,...]=('tsc',)
    render_tools:tuple[str,...]=('remotion',)
    sample_stride:int=30
    max_samples:int=2048
    boundaries:tuple[int,...]=()
    cuts:tuple[int,...]=()
    blank_allowances:tuple[Window,...]=()
    expected_motion:tuple[Window,...]=()
    regions:tuple[RegionExpectation,...]=()
    max_decoded_bytes:int=67108864
    max_process_seconds:int=30
    black_level:int=8
    black_fraction_ppm:int=999000
    uniform_channel_span:int=2
    abrupt_change_ppm:int=300000
    frozen_change_ppm:int=50
    max_repeated_frames:int=30
    duration_tolerance_us:int=2000
    max_receipt_age_seconds:int=3600
    minimum_independent_assessors:int=1
    minimum_review_confidence_ppm:int=900000
    def __post_init__(self):
        token(self.composition_id,'composition');sha256(self.expected_input_digest,'expected_input_digest')
        for n in ('width','height'):integer(getattr(self,n),n,1,8192)
        integer(self.fps_numerator,'fps_numerator',1,240000);integer(self.fps_denominator,'fps_denominator',1,10000)
        f=Fraction(self.fps_numerator,self.fps_denominator)
        if not 1<=f<=240 or (f.numerator,f.denominator)!=(self.fps_numerator,self.fps_denominator):raise ContractError('VIDEO_FPS_NONCANONICAL')
        integer(self.expected_frames,'expected_frames',1,MAX_FRAMES);boolean(self.require_audio,'require_audio')
        for n in ('codecs','pixel_formats','compile_tools','render_tools'):tuple_tokens(getattr(self,n),n,1,32)
        integer(self.sample_stride,'sample_stride',1,MAX_FRAMES);integer(self.max_samples,'max_samples',1,4096)
        for n in ('boundaries','cuts'):
            v=getattr(self,n)
            if type(v) is not tuple or any(type(x) is not int or not 1<=x<self.expected_frames for x in v) or tuple(sorted(set(v)))!=v:raise ContractError('VIDEO_ORDERED_BOUNDARIES',n)
        for n in ('blank_allowances','expected_motion'):
            v=getattr(self,n);records(v,Window,n)
            if tuple(sorted(v,key=lambda x:x.start))!=v or any(x.end>self.expected_frames for x in v) or any(a.end>b.start for a,b in zip(v,v[1:])):raise ContractError('VIDEO_WINDOW_SCOPE',n)
        records(self.regions,RegionExpectation,'regions',0,2048)
        if len({r.region_id for r in self.regions})!=len(self.regions) or any(r.frame>=self.expected_frames for r in self.regions):raise ContractError('VIDEO_REGION_SCOPE')
        integer(self.max_decoded_bytes,'max_decoded_bytes',3,268435456)
        if self.width*self.height*3*self.expected_frames>self.max_decoded_bytes:raise ContractError('VIDEO_DECODE_BUDGET')
        integer(self.max_process_seconds,'max_process_seconds',1,120)
        integer(self.black_level,'black_level',0,254);integer(self.uniform_channel_span,'uniform_span',0,255)
        for n in ('black_fraction_ppm','abrupt_change_ppm','frozen_change_ppm'):integer(getattr(self,n),n,0,1000000)
        integer(self.max_repeated_frames,'max_repeated_frames',1,MAX_FRAMES)
        integer(self.duration_tolerance_us,'duration_tolerance_us',0,1000000)
        integer(self.max_receipt_age_seconds,'max_receipt_age',1,604800)
        integer(self.minimum_independent_assessors,'independent_assessors',1,8)
        integer(self.minimum_review_confidence_ppm,'review_confidence',0,1000000)
    @property
    def fps(self):return Fraction(self.fps_numerator,self.fps_denominator)
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class VideoRequest:
    schema_version:str
    run_id:str
    revision:str
    candidate_digest:str
    composition_id:str
    video:ArtifactRef
    compile_receipt:ArtifactRef
    render_receipt:ArtifactRef
    inputs:tuple[ArtifactRef,...]
    build_outputs:tuple[ArtifactRef,...]
    def __post_init__(self):
        if self.schema_version!=VERSION:raise ContractError('VIDEO_SCHEMA')
        token(self.run_id,'run_id');revision(self.revision);sha256(self.candidate_digest,'candidate_digest');token(self.composition_id,'composition_id')
        for n in ('video','compile_receipt','render_receipt'):
            if type(getattr(self,n)) is not ArtifactRef:raise ContractError('VIDEO_ARTIFACT_TYPE',n)
        if self.video.role!='video':raise ContractError('VIDEO_ARTIFACT_ROLE')
        refs(self.inputs,'inputs',1);refs(self.build_outputs,'build_outputs',1)
        refs(all_refs(self),'all_refs',5)
    @property
    def content_digest(self):return digest(asdict(self))

def all_refs(request):return (request.video,request.compile_receipt,request.render_receipt)+request.inputs+request.build_outputs

@dataclass(frozen=True,slots=True)
class ExecutionReceipt:
    schema_version:str
    stage:str
    run_id:str
    revision:str
    composition_id:str
    inputs_digest:str
    outputs_digest:str
    parent_receipt_sha256:str
    tool_id:str
    tool_version:str
    executable_sha256:str
    command:tuple[str,...]
    environment_digest:str
    exit_code:int
    started:bool
    timed_out:bool
    stdout:ArtifactRef
    stderr:ArtifactRef
    issued_at:int
    execution_kind:str
    mode:str
    first_frame:int
    frame_count:int
    def __post_init__(self):
        if self.schema_version!=VERSION:raise ContractError('VIDEO_RECEIPT_SCHEMA')
        choice(self.stage,('compile','render'),'stage');token(self.run_id,'run_id');revision(self.revision)
        token(self.composition_id,'composition');token(self.tool_id,'tool_id');nonblank(self.tool_version,'tool_version')
        for n in ('inputs_digest','outputs_digest','parent_receipt_sha256','executable_sha256','environment_digest'):sha256(getattr(self,n),n)
        if type(self.command) is not tuple or not 1<=len(self.command)<=128:raise ContractError('VIDEO_COMMAND')
        for v in self.command:nonblank(v,'command',2048)
        integer(self.exit_code,'exit_code',-255,255);boolean(self.started,'started');boolean(self.timed_out,'timed_out')
        for n in ('stdout','stderr'):
            if type(getattr(self,n)) is not ArtifactRef:raise ContractError('VIDEO_LOG_TYPE')
        refs((self.stdout,self.stderr),'logs',2);integer(self.issued_at,'issued_at')
        choice(self.execution_kind,('native','diagnostic','reported'),'execution_kind')
        choice(self.mode,('compile','full','smoke'),'mode')
        integer(self.first_frame,'first_frame',0,MAX_FRAMES-1);integer(self.frame_count,'frame_count',0,MAX_FRAMES)
