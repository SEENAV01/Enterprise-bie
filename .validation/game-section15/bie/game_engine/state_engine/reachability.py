from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from ..ids import require_id
from ..errors import GameContractError
from ..canonical import fingerprint

@dataclass(frozen=True)
class StateNode:
    node_id:str; state_fingerprint:str; terminal:bool=False
    def validate(self):
        require_id(self.node_id,'GAME_STATE_NODE_ID')
        if not isinstance(self.state_fingerprint,str) or not self.state_fingerprint.startswith('sha256:'):raise GameContractError('GAME_STATE_NODE_FINGERPRINT')
        if type(self.terminal) is not bool:raise GameContractError('GAME_STATE_NODE_TERMINAL')
        return self
@dataclass(frozen=True)
class StateEdge:
    edge_id:str; source_id:str; target_id:str; transition_ref:str
    def validate(self):
        for v,c in ((self.edge_id,'GAME_STATE_EDGE_ID'),(self.source_id,'GAME_STATE_EDGE_SOURCE'),(self.target_id,'GAME_STATE_EDGE_TARGET'),(self.transition_ref,'GAME_STATE_EDGE_TRANSITION')):require_id(v,c)
        return self
@dataclass(frozen=True)
class TransitionSystem:
    nodes:tuple[StateNode,...]; edges:tuple[StateEdge,...]; max_nodes:int=1000; product_accepted:bool=False
    def validate(self):
        if not self.nodes:raise GameContractError('GAME_STATE_GRAPH_NODES')
        if type(self.max_nodes) is not int or self.max_nodes<=0 or len(self.nodes)>self.max_nodes:raise GameContractError('GAME_STATE_GRAPH_BUDGET')
        for n in self.nodes:n.validate()
        ids=[n.node_id for n in self.nodes]
        if len(ids)!=len(set(ids)):raise GameContractError('GAME_STATE_GRAPH_DUP_NODE')
        known=set(ids);eids=[]
        for e in self.edges:
            e.validate();eids.append(e.edge_id)
            if e.source_id not in known or e.target_id not in known:raise GameContractError('GAME_STATE_GRAPH_MISSING_NODE')
        if len(eids)!=len(set(eids)):raise GameContractError('GAME_STATE_GRAPH_DUP_EDGE')
        if self.product_accepted is not False:raise GameContractError('GAME_PRODUCT_ACCEPTANCE_FORBIDDEN')
        return self

def analyze_reachability(system:TransitionSystem,start_id:str,target_ids):
    system.validate();known={n.node_id:n for n in system.nodes};require_id(start_id,'GAME_STATE_GRAPH_START')
    targets=set(target_ids)
    if start_id not in known or not targets or not targets<=set(known):raise GameContractError('GAME_STATE_GRAPH_QUERY')
    adj={k:[] for k in known}
    for e in sorted(system.edges,key=lambda x:x.edge_id):adj[e.source_id].append(e.target_id)
    q=deque([start_id]);parent={start_id:None};order=[]
    while q:
        n=q.popleft();order.append(n)
        for x in sorted(adj[n]):
            if x not in parent:parent[x]=n;q.append(x)
    reached=sorted(targets&set(parent));unreachable=sorted(targets-set(parent));paths={}
    for t in reached:
        p=[];x=t
        while x is not None:p.append(x);x=parent[x]
        paths[t]=list(reversed(p))
    dead_ends=sorted(n for n in parent if not adj[n] and not known[n].terminal)
    # cycle detection on reachable subgraph
    visiting=set();done=set();cycles=[]
    def dfs(n,path):
        if n in visiting:
            i=path.index(n);cycles.append(tuple(path[i:]+[n]));return
        if n in done:return
        visiting.add(n)
        for x in sorted(adj[n]):
            if x in parent:dfs(x,path+[x])
        visiting.remove(n);done.add(n)
    dfs(start_id,[start_id])
    return {'start_id':start_id,'targets':sorted(targets),'reached':reached,'unreachable':unreachable,'paths':paths,'visited_order':order,'dead_ends':dead_ends,'cycles':sorted(set(cycles)),'graph_fingerprint':fingerprint(system),'product_accepted':False}
