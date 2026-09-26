from collections import deque
from .common import *
def define(ctx):return make_definition(ctx,'mechanic:graph-exploration',MechanicKind.GRAPH_EXPLORATION,'Learner explores relationships by expanding nodes/edges with deterministic graph traversal and semantic highlighting.',(action('select:node',ActionKind.SELECT,'Select graph node','Tab then Enter','graph:node'),),(motion('motion:trace',MotionSemantic.TRACE,'graph:edges','Trace only the relationships currently explored.','graph_state'),),('semantic_motion','keyboard_input','state_machine','graph'))
def execute(ctx,state,graph,start,target=None):
 d=define(ctx)
 if not isinstance(graph,dict) or start not in graph:raise MechanicError('GAME_MECH_GRAPH_INPUT')
 nodes=set(graph)|{x for v in graph.values() for x in v}
 if any(x not in nodes for v in graph.values() for x in v):raise MechanicError('GAME_MECH_GRAPH_NODE')
 q=deque([start]);seen=[];parent={start:None}
 while q:
  n=q.popleft()
  if n in seen:continue
  seen.append(n)
  for x in sorted(graph.get(n,())):
   if x not in parent:parent[x]=n
   q.append(x)
 path=()
 if target is not None:
  if target not in parent:raise MechanicError('GAME_MECH_GRAPH_UNREACHABLE')
  cur=target;tmp=[]
  while cur is not None:tmp.append(cur);cur=parent[cur]
  path=tuple(reversed(tmp))
 after={**state,'visited':tuple(seen),'path':path};out={'visited':tuple(seen),'path':path,'edge_count':sum(len(v) for v in graph.values())};return after,out,receipt(d,state,after,{'start':start,'target':target},out)
