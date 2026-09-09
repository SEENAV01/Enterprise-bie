def transaction_boundary(name,resources,
                        atomic=False):
    return {"name":name,"resources":resources,
            "atomic":atomic}

def is_distributed(boundary):
    return len(boundary.get("resources",[])) > 1
