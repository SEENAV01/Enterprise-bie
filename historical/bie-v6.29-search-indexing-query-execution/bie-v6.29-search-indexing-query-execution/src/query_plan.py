def query_plan(stages,
               estimated_cost=0):
    return {"stages":stages,
            "estimated_cost":estimated_cost}

def valid(record):
    return bool(record["stages"]) and record["estimated_cost"]>=0
