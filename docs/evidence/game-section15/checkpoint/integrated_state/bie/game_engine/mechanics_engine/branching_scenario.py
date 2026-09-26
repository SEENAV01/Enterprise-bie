from .common import *
def define(ctx):return make_definition(ctx,'mechanic:branching-scenario',MechanicKind.BRANCHING_SCENARIO,'Learner makes consequential decisions through an explicit finite branch graph with no dangling outcomes.',(action('select:branch',ActionKind.SELECT,'Choose scenario action','Arrow keys then Enter','scenario:choices'),),(motion('motion:branch',MotionSemantic.BRANCH,'scenario:choices','Reveal the causal consequence of the learner decision.','branch_state'),),('semantic_motion','keyboard_input','state_machine'))
def _validate(graph):
 nodes=set(graph)
 for n,choices in graph.items():
  if not choices:raise MechanicError('GAME_MECH_BRANCH_DEAD_NODE',n)
  for target in choices.values():
   if target not in nodes and not str(target).startswith('terminal:'):raise MechanicError('GAME_MECH_BRANCH_DANGLING',str(target))
def execute(ctx,state,graph,node,choice):
 d=define(ctx);_validate(graph)
 if node not in graph or choice not in graph[node]:raise MechanicError('GAME_MECH_BRANCH_INVALID_CHOICE')
 target=graph[node][choice];after={**state,'node':target,'terminal':str(target).startswith('terminal:')};out={'from':node,'choice':choice,'to':target,'terminal':after['terminal']};return after,out,receipt(d,state,after,{'node':node,'choice':choice},out)
