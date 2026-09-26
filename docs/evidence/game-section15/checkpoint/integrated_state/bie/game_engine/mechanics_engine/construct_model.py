from .common import *
from .input_contracts import ModelPart
def define(ctx):return make_definition(ctx,'mechanic:construct-model',MechanicKind.CONSTRUCT_MODEL,'Learner assembles a model whose dependency structure mirrors the concept being learned.',(action('place:part',ActionKind.PLACE,'Attach the selected part','Arrow keys then Enter','model:assembly'),),(motion('motion:assemble',MotionSemantic.ASSEMBLE,'model:assembly','Visualize structural dependency as parts are assembled.','assembly'),),('semantic_motion','keyboard_input','state_machine'))
def _order(parts):
 typed=tuple(ModelPart.from_mapping(x) for x in parts);ids={p.part_id for p in typed}
 if len(ids)!=len(typed):raise MechanicError('GAME_MECH_MODEL_DUPLICATE_PART')
 deps={p.part_id:set(p.requires) for p in typed}
 if any(x not in ids for s in deps.values() for x in s):raise MechanicError('GAME_MECH_MODEL_MISSING_DEPENDENCY')
 out=[]
 while deps:
  ready=sorted(k for k,v in deps.items() if not v)
  if not ready:raise MechanicError('GAME_MECH_MODEL_CYCLE')
  n=ready[0];out.append(n);deps.pop(n)
  for v in deps.values():v.discard(n)
 return tuple(out)
def execute(ctx,state,parts,learner_order):
 d=define(ctx);canonical=_order(parts);valid=tuple(learner_order)==canonical;after={**state,'assembly':tuple(learner_order),'valid':valid};out={'required_order':canonical,'valid':valid};return after,out,receipt(d,state,after,{'learner_order':tuple(learner_order)},out)
