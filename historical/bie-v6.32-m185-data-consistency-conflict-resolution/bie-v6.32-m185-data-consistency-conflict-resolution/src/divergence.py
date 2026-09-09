def divergence(key,node_a,node_b,
                difference_count):
    return {"key":key,"node_a":node_a,
            "node_b":node_b,
            "difference_count":difference_count,
            "status":"DIVERGENT" if difference_count else "CONVERGED"}

def converged(record):
    return record["status"]=="CONVERGED"
