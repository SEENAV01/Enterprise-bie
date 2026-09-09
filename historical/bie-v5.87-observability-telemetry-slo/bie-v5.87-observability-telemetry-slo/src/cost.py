def cost_metric(operation,input_cost=0,
                output_cost=0,infra_cost=0):
    return {"operation":operation,
            "input_cost":input_cost,
            "output_cost":output_cost,
            "infra_cost":infra_cost,
            "total_cost":input_cost+output_cost+infra_cost}
