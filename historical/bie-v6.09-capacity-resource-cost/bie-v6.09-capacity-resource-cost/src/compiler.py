from resource import resource
from quota import quota
from rate_limit import rate_limit
from concurrency import concurrency_limit
from autoscaling import autoscaling_policy
from budget import resource_budget
from cost import cost_record
from governance import resource_policy

def compile_capacity(service,tenant_id):
    r=resource(service,"compute","COMPUTE",100,"units",60)
    q=quota(tenant_id,"compute",100,"units","1h")
    rl=rate_limit(service,1000,60,100)
    cc=concurrency_limit(service,50,100)
    scale=autoscaling_policy(service,2,20,.70)
    b=resource_budget(service,100,1000,100000)
    c=cost_record(service,"current",10,2,1,3)
    p=resource_policy(service,[q],[rl],[cc],[b])
    return {"schema_version":"6.09",
            "resource":r,"quota":q,
            "rate_limit":rl,"concurrency":cc,
            "autoscaling":scale,
            "budget":b,"cost":c,
            "policy":p,
            "quality_gate":{"valid":True,"errors":[]}}
