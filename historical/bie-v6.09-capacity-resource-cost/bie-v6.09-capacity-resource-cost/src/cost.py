def cost_record(service,period,
               compute_cost=0,
               storage_cost=0,
               network_cost=0,
               request_cost=0):
    total=(compute_cost+storage_cost+
           network_cost+request_cost)
    return {"service":service,"period":period,
            "compute_cost":compute_cost,
            "storage_cost":storage_cost,
            "network_cost":network_cost,
            "request_cost":request_cost,
            "total_cost":total}

def cost_per_unit(total_cost,units):
    return 0 if units<=0 else total_cost/units
