from __future__ import annotations
from collections import deque
from .contracts import LevelNode
from ..errors import GameContractError

def validate_level_graph(levels:tuple[LevelNode,...]):
    if not levels:raise GameContractError('GAME_DIR_LEVEL_GRAPH_EMPTY')
    ids=[x.level_id for x in levels]
    if len(ids)!=len(set(ids)):raise GameContractError('GAME_DIR_LEVEL_GRAPH_DUPLICATE')
    known=set(ids);indegree={x:0 for x in ids};children={x:[] for x in ids}
    for level in levels:
        for parent in level.prerequisite_level_ids:
            if parent not in known:raise GameContractError('GAME_DIR_LEVEL_GRAPH_MISSING_PREREQUISITE',parent)
            if parent==level.level_id:raise GameContractError('GAME_DIR_LEVEL_GRAPH_SELF_EDGE',parent)
            indegree[level.level_id]+=1;children[parent].append(level.level_id)
    q=deque(sorted(x for x,v in indegree.items() if v==0));order=[]
    while q:
        n=q.popleft();order.append(n)
        for child in sorted(children[n]):
            indegree[child]-=1
            if indegree[child]==0:q.append(child)
    if len(order)!=len(ids):raise GameContractError('GAME_DIR_LEVEL_GRAPH_CYCLE')
    return tuple(order)

def validate_progression(levels):
    order=validate_level_graph(tuple(levels));index={x:i for i,x in enumerate(order)}
    for level in levels:
        if any(index[p]>=index[level.level_id] for p in level.prerequisite_level_ids):raise GameContractError('GAME_DIR_LEVEL_GRAPH_ORDER')
    return order
