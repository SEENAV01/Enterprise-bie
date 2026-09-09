def critical_path(nodes, edges, durations):
    preds={n["id"]:[] for n in nodes}
    for e in edges: preds[e["target"]].append(e["source"])
    memo={}
    def cost(n):
        if n in memo:return memo[n]
        memo[n]=durations.get(n,1)+max((cost(p) for p in preds[n]),default=0)
        return memo[n]
    vals={n["id"]:cost(n["id"]) for n in nodes}
    end=max(vals,key=vals.get) if vals else None
    return {"finish_time":vals.get(end,0),"terminal_node":end,"path_metric":vals}

def concurrency_limit(queue_depth, max_parallel, active):
    return max(0,min(max_parallel,queue_depth+max_parallel-active))
