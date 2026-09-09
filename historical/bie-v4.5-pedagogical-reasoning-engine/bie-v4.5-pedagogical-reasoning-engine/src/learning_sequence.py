def build_learning_sequence(items, dependency_order):
    rank={x:i for i,x in enumerate(dependency_order)}
    return sorted(items,key=lambda x:(rank.get(x["id"],10**9),
                                      -float(x.get("importance_score",0))))
