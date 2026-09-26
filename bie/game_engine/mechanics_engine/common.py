from __future__ import annotations
from typing import Any
from ..canonical import fingerprint
from ..interaction import ActionKind
from ..provenance import EvidenceRef,ProvenanceBundle
from .contracts import *
from .errors import MechanicError

def sample_provenance(objective='objective:motion'):
    return ProvenanceBundle((EvidenceRef('source:book:p1','source:book:p1','1'*64,'source'),EvidenceRef('reason:game:1','reason:game:1','2'*64,'reasoning'),EvidenceRef(objective,objective,'3'*64,'objective')))
def sample_context(objective='objective:motion'):
    return MechanicContext(objective,('source:book:p1',),('reason:game:1',),sample_provenance(objective),('semantic_motion','keyboard_input','state_machine','deterministic_replay','graph','map','equation','simulation')).validate()
def require_runtime(ctx:MechanicContext,*caps):
    ctx.validate();missing=[c for c in caps if c not in ctx.runtime_capabilities]
    if missing:raise MechanicError('GAME_MECH_RUNTIME_MISSING',','.join(missing))
def make_definition(ctx,mid,kind,intent,actions,motion,caps,policy=ReplayPolicy.EXACT):
    ctx.validate();require_runtime(ctx,*caps)
    d=MechanicDefinition(mid,kind,ctx.objective_id,intent,tuple(actions),tuple(motion),tuple(caps),tuple(ctx.source_refs+ctx.reasoning_refs+(ctx.objective_id,)),policy,True)
    return d.validate()
def action(aid,kind,label,key,target):return AccessibilityAction(aid,kind,label,key,target).validate()
def motion(mid,semantic,target,purpose,binding=None):return SemanticMotion(mid,semantic,target,purpose,binding).validate()
def receipt(defn,before,after,action_payload,outcome):
    if before==after:raise MechanicError('GAME_MECH_NO_STATE_CHANGE')
    body={'mechanic':defn.mechanic_id,'before':before,'after':after,'action':action_payload,'outcome':outcome}
    rid='mechanic:'+fingerprint(body)[7:31]
    r=MechanicReceipt(rid,defn.mechanic_id,defn.kind,fingerprint(before),fingerprint(after),fingerprint(action_payload),fingerprint(outcome),True,tuple(m.motion_id for m in defn.motion),defn.evidence_refs,True,True,False)
    return r.validate()
def bounded_number(v,lo,hi,code):
    if type(v) not in (int,float) or isinstance(v,bool) or not lo<=v<=hi:raise MechanicError(code)
    return float(v)
