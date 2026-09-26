from .common import *
from .input_contracts import RetrievalItem
def define(ctx):return make_definition(ctx,'mechanic:retrieval',MechanicKind.RETRIEVAL,'Learner actively retrieves grounded knowledge before feedback; prompt scheduling is deterministic and answer-safe.',(action('type:response',ActionKind.TYPE,'Enter response','Keyboard input','retrieval:response'),action('submit:response',ActionKind.SUBMIT,'Submit response','Enter','retrieval:submit')),(motion('motion:focus',MotionSemantic.FOCUS,'retrieval:prompt','Focus attention on the prompt and later evidence-backed feedback.','retrieval_state'),),('semantic_motion','keyboard_input','state_machine'),ReplayPolicy.SEEDED)
def select_item(pool,history):
 if not pool:raise MechanicError('GAME_MECH_RETRIEVAL_POOL')
 typed=tuple(RetrievalItem.from_mapping(x) for x in pool);ids=[x.item_id for x in typed]
 if len(ids)!=len(set(ids)):raise MechanicError('GAME_MECH_RETRIEVAL_ITEM')
 counts={i:history.count(i) for i in ids};return sorted(ids,key=lambda i:(counts[i],i))[0]
def execute(ctx,state,pool,history,response_submitted=False):
 d=define(ctx);selected=select_item(pool,history);row=RetrievalItem.from_mapping(next(x for x in pool if x['id']==selected))
 if not response_submitted:
  after={**state,'prompt_id':selected,'answer_revealed':False};out={'prompt_ref':row.prompt_ref,'answer_ref':None,'evidence_ref':row.evidence_ref,'answer_revealed':False}
 else:
  after={**state,'prompt_id':selected,'answer_revealed':True};out={'prompt_ref':row.prompt_ref,'answer_ref':row.answer_ref,'evidence_ref':row.evidence_ref,'answer_revealed':True}
 return after,out,receipt(d,state,after,{'selected':selected,'submitted':response_submitted},out)
