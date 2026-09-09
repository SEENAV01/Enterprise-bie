def causal_relation(relation_id,cause,effect,mechanism,
                    conditions=None):
    return {
      "relation_id":relation_id,"cause":cause,"effect":effect,
      "mechanism":mechanism,"conditions":conditions or []
    }

def causal_graph(relations):
    return [{"from":r["cause"],"to":r["effect"],
             "mechanism":r["mechanism"]} for r in relations]
