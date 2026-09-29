"""QA-GAME001..004: immutable evidence, operator-owned finite state/learning oracle.

DOM observations are externally collected, not a game's self-reported PASS. All
bounds are intentionally finite. A game may have loops; test paths are bounded.
"""
from __future__ import annotations
from dataclasses import dataclass,asdict
from urllib.parse import urlparse
from ..release_v2.contracts import (ArtifactRef,ContractError,token,integer,sha256,
    revision,choice,tuple_tokens,safe_relative_path,digest)
from ..source_v2.models import Request as SourceRequest,Policy as SourcePolicy,text

def seq(v,cls,name,lo=0,hi=512):
    if type(v) is not tuple or not lo<=len(v)<=hi or any(type(x) is not cls for x in v):raise ContractError('GAME_COLLECTION',name)
def unique(v,key,name):
    if len({getattr(x,key) for x in v})!=len(v):raise ContractError('GAME_DUPLICATE',name)
def string(v,name,limit=16384):
    if type(v) is not str or len(v)>limit or '\x00' in v:raise ContractError('GAME_STRING',name)
    try:v.encode('utf-8')
    except UnicodeError as e:raise ContractError('GAME_UNICODE',name) from e

def refs(v,name,lo=1):
    seq(v,ArtifactRef,name,lo,512);unique(v,'artifact_id',name);unique(v,'path',name)
def inventory(v):return digest([asdict(x) for x in sorted(v,key=lambda a:a.path)])

@dataclass(frozen=True,slots=True)
class Value:
    key:str
    text:str
    def __post_init__(self):token(self.key,'value.key');string(self.text,'value.text')

@dataclass(frozen=True,slots=True)
class State:
    state_id:str
    values:tuple[Value,...]
    terminal:bool
    successful:bool
    def __post_init__(self):
        token(self.state_id,'state');seq(self.values,Value,'values',1,64);unique(self.values,'key','values')
        if type(self.terminal) is not bool or type(self.successful) is not bool:raise ContractError('GAME_BOOLEAN')
        if self.successful and not self.terminal:raise ContractError('GAME_SUCCESS_NOT_TERMINAL')

@dataclass(frozen=True,slots=True)
class Observable:
    key:str
    selector:str
    def __post_init__(self):token(self.key,'observable.key');text(self.selector,'selector',256)

@dataclass(frozen=True,slots=True)
class Action:
    action_id:str
    kind:str
    selector:str
    value:str
    def __post_init__(self):
        token(self.action_id,'action');choice(self.kind,('click','press','fill','drag','reload'),'action.kind')
        string(self.selector,'selector',256);string(self.value,'value',1024)
        if self.kind!='reload' and not self.selector.strip():raise ContractError('GAME_ACTION_SELECTOR')
        if self.kind in ('press','drag') and not self.value:raise ContractError('GAME_ACTION_ARGUMENT')
        if self.kind in ('click','reload') and self.value:raise ContractError('GAME_ACTION_UNUSED_VALUE')
        if self.kind=='reload' and self.selector:raise ContractError('GAME_RELOAD_SELECTOR')

@dataclass(frozen=True,slots=True)
class Transition:
    transition_id:str
    before:str
    action_id:str
    after:str
    def __post_init__(self):
        for k in ('transition_id','before','action_id','after'):token(getattr(self,k),k)

@dataclass(frozen=True,slots=True)
class Scenario:
    scenario_id:str
    width:int
    height:int
    action_ids:tuple[str,...]
    def __post_init__(self):
        token(self.scenario_id,'scenario');integer(self.width,'width',160,4096);integer(self.height,'height',120,4096)
        seq(self.action_ids,str,'actions',1,128)
        for x in self.action_ids:token(x,'scenario.action') # repeats are deliberate, e.g. double submit

@dataclass(frozen=True,slots=True)
class LearningTarget:
    objective_id:str
    challenge_id:str
    mechanic:str
    prompt_claim_id:str
    prompt_key:str
    correct_claim_id:str
    incorrect_claim_id:str
    feedback_key:str
    response_action_ids:tuple[str,...]
    success_state:str
    failure_state:str
    def __post_init__(self):
        for k in ('objective_id','challenge_id','mechanic','prompt_claim_id','prompt_key','correct_claim_id','incorrect_claim_id','feedback_key','success_state','failure_state'):token(getattr(self,k),k)
        tuple_tokens(self.response_action_ids,'response_actions',1,64)
        if self.success_state==self.failure_state:raise ContractError('GAME_LEARNING_OUTCOMES_IDENTICAL')

@dataclass(frozen=True,slots=True)
class TextBinding:
    claim_id:str
    key:str
    state_ids:tuple[str,...]
    def __post_init__(self):
        token(self.claim_id,'binding.claim');token(self.key,'binding.key');tuple_tokens(self.state_ids,'binding.states',1,128)

@dataclass(frozen=True,slots=True)
class GamePolicy:
    policy_id:str
    game_id:str
    expected_input_digest:str
    entrypoint:str
    required_loaded_paths:tuple[str,...]
    initial_state:str
    observables:tuple[Observable,...]
    states:tuple[State,...]
    actions:tuple[Action,...]
    transitions:tuple[Transition,...]
    scenarios:tuple[Scenario,...]
    learning:tuple[LearningTarget,...]
    text_bindings:tuple[TextBinding,...]
    source:SourcePolicy
    replays:int=2
    max_action_ms:int=5000
    max_receipt_age_seconds:int=86400
    minimum_review_confidence_ppm:int=950000
    minimum_independent_assessors:int=1
    compile_tools:tuple[str,...]=('tsc',)
    def __post_init__(self):
        token(self.policy_id,'policy');token(self.game_id,'game');sha256(self.expected_input_digest,'inputs');safe_relative_path(self.entrypoint)
        seq(self.required_loaded_paths,str,'required_loaded',1,128)
        if len(set(self.required_loaded_paths))!=len(self.required_loaded_paths):raise ContractError('GAME_DUPLICATE_REQUIRED_PATH')
        for p in self.required_loaded_paths:safe_relative_path(p)
        if self.entrypoint not in self.required_loaded_paths:raise ContractError('GAME_ENTRY_NOT_REQUIRED')
        token(self.initial_state,'initial');integer(self.replays,'replays',2,4);integer(self.max_action_ms,'max_action_ms',1,30000)
        integer(self.max_receipt_age_seconds,'max_age',1,604800);integer(self.minimum_review_confidence_ppm,'confidence',900000,1000000);integer(self.minimum_independent_assessors,'assessors',1,4)
        tuple_tokens(self.compile_tools,'compile_tools',1,16)
        if type(self.source) is not SourcePolicy:raise ContractError('GAME_SOURCE_POLICY')
        for k,cls,field,hi in [('observables',Observable,'key',64),('states',State,'state_id',128),('actions',Action,'action_id',128),('transitions',Transition,'transition_id',512),('scenarios',Scenario,'scenario_id',64),('learning',LearningTarget,'challenge_id',64)]:
            v=getattr(self,k);seq(v,cls,k,1,hi);unique(v,field,k)
        if len({o.selector for o in self.observables})!=len(self.observables):raise ContractError('GAME_OBSERVABLE_ALIAS')
        states={s.state_id:s for s in self.states};actions={a.action_id for a in self.actions};obs={o.key for o in self.observables}
        if self.initial_state not in states:raise ContractError('GAME_INITIAL_MISSING')
        for s in self.states:
            if {v.key for v in s.values}!=obs:raise ContractError('GAME_STATE_OBSERVABLE_SCOPE')
        if len({digest(sorted((v.key,v.text) for v in s.values)) for s in self.states})!=len(self.states):raise ContractError('GAME_INDISTINGUISHABLE_STATES')
        if len({(t.before,t.action_id) for t in self.transitions})!=len(self.transitions):raise ContractError('GAME_NONDETERMINISTIC_ORACLE')
        for t in self.transitions:
            if t.before not in states or t.after not in states or t.action_id not in actions:raise ContractError('GAME_TRANSITION_REFERENCE')
        for s in self.scenarios:
            if not set(s.action_ids)<=actions:raise ContractError('GAME_SCENARIO_REFERENCE')
        seq(self.text_bindings,TextBinding,'text_bindings',0,128)
        for b in self.text_bindings:
            if b.key not in obs or not set(b.state_ids)<=set(states):raise ContractError('GAME_TEXT_BINDING_REFERENCE')
        for t in self.learning:
            if t.success_state not in states or t.failure_state not in states or not set(t.response_action_ids)<=actions or t.prompt_key not in obs or t.feedback_key not in obs:raise ContractError('GAME_LEARNING_REFERENCE')
            if not states[t.success_state].successful or states[t.failure_state].successful:raise ContractError('GAME_LEARNING_SUCCESS_ORACLE')
    @property
    def content_digest(self):return digest(asdict(self))
    @property
    def oracle_digest(self):
        d=asdict(self);d.pop('expected_input_digest');d.pop('source');return digest(d)

@dataclass(frozen=True,slots=True)
class GameRequest:
    run_id:str
    revision:str
    candidate_digest:str
    game_id:str
    inputs:tuple[ArtifactRef,...]
    outputs:tuple[ArtifactRef,...]
    build_receipt:ArtifactRef
    runtime_receipt:ArtifactRef
    source:SourceRequest
    def __post_init__(self):
        token(self.run_id,'run');revision(self.revision);sha256(self.candidate_digest,'candidate');token(self.game_id,'game')
        refs(self.inputs,'inputs');refs(self.outputs,'outputs')
        if type(self.build_receipt) is not ArtifactRef or type(self.runtime_receipt) is not ArtifactRef or type(self.source) is not SourceRequest:raise ContractError('GAME_REQUEST_TYPES')
        if (self.source.run_id,self.source.revision,self.source.candidate_digest)!=(self.run_id,self.revision,self.candidate_digest):raise ContractError('GAME_SOURCE_CONTEXT')
        validate_aliases(all_refs(self))
    @property
    def content_digest(self):return digest(asdict(self))

@dataclass(frozen=True,slots=True)
class BuildReceipt:
    schema_version:str
    run_id:str
    revision:str
    game_id:str
    inputs_digest:str
    outputs_digest:str
    entrypoint:str
    tool_id:str
    tool_version:str
    started:bool
    exit_code:int
    timed_out:bool
    issued_at:int
    execution_kind:str
    stdout:ArtifactRef
    stderr:ArtifactRef
    def __post_init__(self):
        if self.schema_version!='bie.qa.game-build/1':raise ContractError('GAME_BUILD_SCHEMA')
        token(self.run_id,'run');revision(self.revision);token(self.game_id,'game')
        for k in ('inputs_digest','outputs_digest'):sha256(getattr(self,k),k)
        safe_relative_path(self.entrypoint);token(self.tool_id,'tool');text(self.tool_version,'tool_version',256)
        if type(self.started) is not bool or type(self.timed_out) is not bool:raise ContractError('GAME_BOOLEAN')
        integer(self.exit_code,'exit_code',-255,255);integer(self.issued_at,'issued_at')
        choice(self.execution_kind,('native','authored_diagnostic','reported'),'execution_kind')
        for r in (self.stdout,self.stderr):
            if type(r) is not ArtifactRef:raise ContractError('GAME_LOG_REFERENCE')

@dataclass(frozen=True,slots=True)
class ObservedValue:
    key:str
    text:str
    count:int
    visible:bool
    def __post_init__(self):
        token(self.key,'key');string(self.text,'observed.text');integer(self.count,'count',0,10000)
        if type(self.visible) is not bool:raise ContractError('GAME_BOOLEAN')

@dataclass(frozen=True,slots=True)
class Step:
    action_id:str
    start_ms:int
    end_ms:int
    succeeded:bool
    error:str
    values:tuple[ObservedValue,...]
    screenshot:ArtifactRef
    def __post_init__(self):
        token(self.action_id,'step.action');integer(self.start_ms,'start_ms',0,3600000);integer(self.end_ms,'end_ms',self.start_ms,3600000)
        if type(self.succeeded) is not bool:raise ContractError('GAME_BOOLEAN')
        string(self.error,'error',4096);seq(self.values,ObservedValue,'observed.values',1,64);unique(self.values,'key','observed.values')
        if type(self.screenshot) is not ArtifactRef:raise ContractError('GAME_SCREENSHOT_REF')

@dataclass(frozen=True,slots=True)
class Trace:
    scenario_id:str
    replay:int
    width:int
    height:int
    steps:tuple[Step,...]
    loaded_paths:tuple[str,...]
    def __post_init__(self):
        token(self.scenario_id,'scenario');integer(self.replay,'replay',0,3);integer(self.width,'width',1,4096);integer(self.height,'height',1,4096);seq(self.steps,Step,'steps',1,129)
        seq(self.loaded_paths,str,'trace.loaded',0,512)
        if len(set(self.loaded_paths))!=len(self.loaded_paths):raise ContractError('GAME_TRACE_LOADED_DUPLICATE')
        for x in self.loaded_paths:safe_relative_path(x)

@dataclass(frozen=True,slots=True)
class LoadedAsset:
    path:str
    sha256:str
    size:int
    def __post_init__(self):safe_relative_path(self.path);sha256(self.sha256,'loaded.sha');integer(self.size,'loaded.size',1,16777216)

@dataclass(frozen=True,slots=True)
class RuntimeReceipt:
    schema_version:str
    run_id:str
    revision:str
    game_id:str
    build_receipt_sha256:str
    outputs_digest:str
    oracle_digest:str
    entrypoint:str
    origin:str
    method:str
    browser_version:str
    issued_at:int
    execution_kind:str
    sandbox_verified:bool
    loaded:tuple[LoadedAsset,...]
    traces:tuple[Trace,...]
    page_errors:tuple[str,...]
    console_errors:tuple[str,...]
    network_violations:tuple[str,...]
    def __post_init__(self):
        if self.schema_version!='bie.qa.game-runtime/1':raise ContractError('GAME_RUNTIME_SCHEMA')
        token(self.run_id,'run');revision(self.revision);token(self.game_id,'game')
        for k in ('build_receipt_sha256','outputs_digest','oracle_digest'):sha256(getattr(self,k),k)
        safe_relative_path(self.entrypoint);string(self.origin,'origin',2048)
        choice(self.method,('http_entrypoint','injected_bundle','reported'),'method');text(self.browser_version,'browser',256);integer(self.issued_at,'issued_at')
        choice(self.execution_kind,('native','authored_diagnostic','reported'),'execution_kind')
        if type(self.sandbox_verified) is not bool:raise ContractError('GAME_BOOLEAN')
        seq(self.loaded,LoadedAsset,'loaded',0,512);unique(self.loaded,'path','loaded');seq(self.traces,Trace,'traces',0,256)
        if len({(t.scenario_id,t.replay) for t in self.traces})!=len(self.traces):raise ContractError('GAME_DUPLICATE_TRACE')
        if sum(len(t.steps) for t in self.traces)>4096:raise ContractError('GAME_TOTAL_STEP_BUDGET')
        for k in ('page_errors','console_errors','network_violations'):
            seq(getattr(self,k),str,k,0,256)
            for x in getattr(self,k):string(x,k,4096)

def all_refs(r):
    return r.inputs+r.outputs+(r.build_receipt,r.runtime_receipt)+tuple(s.artifact for s in r.source.sources)+tuple(o.artifact for o in r.source.outputs)
def validate_aliases(values):
    ids={};paths={}
    for r in values:
        if (r.artifact_id in ids and ids[r.artifact_id]!=r) or (r.path in paths and paths[r.path]!=r):raise ContractError('GAME_ARTIFACT_ALIAS')
        ids[r.artifact_id]=r;paths[r.path]=r
