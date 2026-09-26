from __future__ import annotations
from ..fixtures import sample_document
from ..mechanics_engine.parameter import define as define_parameter,execute as execute_parameter
from ..mechanics_engine.common import sample_context as mechanic_context
from ..mechanics_engine.semantic_events import from_receipt
from .contracts import *
def compiler_context():
    doc=sample_document();mctx=mechanic_context();d=define_parameter(mctx);_,_,r=execute_parameter(mctx,{'value':1.0},1.0,(0,10));event=from_receipt(d,r)
    texts={'text:success':'Correct. The object reached the target because the state changed to x equals 2.','text:failure':'Not yet. Compare the current position with the target.','text:misdirection':'Check which direction moves x toward the target.','text:explanation':'Changing x changes the object position represented by the semantic visual.'}
    scoring={'policy:score:v1':ScoringPolicy('policy:score:v1',10,0,1,0,True,False)};mastery={'policy:mastery:v1':MasteryPolicy('policy:mastery:v1',.8,1)}
    assets={'asset:sfx:success':AssetDescriptor('asset:sfx:success','audio/wav','4'*64,'Success sound')}
    return CompilerContext(doc,texts,scoring,mastery,assets,(event,),('typescript','html','state_machine','semantic_motion','keyboard_input','deterministic_replay'),('game_started','challenge_completed','mechanic_completed'),CompilerSecurityPolicy(),'studio-enterprise-v1',False).validate()
