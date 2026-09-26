from .common import *
def define(ctx):return make_definition(ctx,'mechanic:sequencing',MechanicKind.SEQUENCING,'Learner reconstructs a dependency-respecting sequence rather than memorizing display order.',(action('order:items',ActionKind.ORDER,'Reorder the items','Arrow keys and Enter','sequence:list'),),(motion('motion:order',MotionSemantic.REORDER,'sequence:list','Animate only learner-driven sequence changes.','sequence'),),('semantic_motion','keyboard_input','state_machine'))
def _topo(items,deps):
 inc={x:set(deps.get(x,())) for x in items}
 if any(y not in inc for s in inc.values() for y in s):raise MechanicError('GAME_MECH_SEQUENCE_UNKNOWN_DEPENDENCY')
 out=[]
 while inc:
  ready=sorted(x for x,v in inc.items() if not v)
  if not ready:raise MechanicError('GAME_MECH_SEQUENCE_CYCLE')
  n=ready[0];out.append(n);inc.pop(n)
  for v in inc.values():v.discard(n)
 return tuple(out)
def execute(ctx,state,items,deps,learner_order):
 d=define(ctx);canonical=_topo(tuple(items),deps)
 if tuple(sorted(learner_order))!=tuple(sorted(items)) or len(set(learner_order))!=len(items):raise MechanicError('GAME_MECH_SEQUENCE_COVERAGE')
 valid=all(learner_order.index(p)<learner_order.index(x) for x in items for p in deps.get(x,()))
 after={**state,'sequence':tuple(learner_order),'valid':valid};out={'canonical_example':canonical,'valid':valid,'dependency_count':sum(len(x) for x in deps.values())};return after,out,receipt(d,state,after,{'learner_order':tuple(learner_order)},out)
