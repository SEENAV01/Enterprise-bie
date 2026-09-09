from registry import register_model
from routing import route
from policy import choose_policy,budget_allows,latency_allows
from inference import create_inference_job,start_job,complete_job
from fallback import fallback_chain,choose_fallback
from cache import cache_key,get_cached,put_cached

def build_m274_runtime():
    registry={}
    primary=register_model(registry,"reasoner","v3",["reasoning","planning"],"provider-a",0.03)
    fallback=register_model(registry,"reasoner-lite","v2",["reasoning","planning"],"provider-b",0.01)
    models=list(registry.values())
    policy=choose_policy({"task_type":"course_planning"},[
        {"task_type":"course_planning","priority":10,"budget":0.10,"max_latency":500}
    ])
    selected=route(models,"planning",max_cost=0.05,preferred_provider="provider-a")
    job=create_inference_job("infer-001",selected,"Create lesson plan",0.03,300)
    allowed=budget_allows(policy,job["estimated_cost"],0) and latency_allows(policy,job["estimated_latency"])
    started=start_job(job)
    completed=complete_job(started,{"plan":"lesson-plan-v1"})
    cache={}; key=cache_key(selected["model_id"],selected["version"],job["prompt"])
    put_cached(cache,key,completed["output"]); cached=get_cached(cache,key)
    chain=fallback_chain(models,"planning")
    fallback_choice=choose_fallback(chain,selected["model_id"])
    return {"schema_version":"7.21","registry":models,"policy":policy,
            "routing":{"selected":selected,"allowed":allowed},
            "inference_job":completed,"cache":{"key":key,"hit":cached is not None},
            "fallback":{"chain":chain,"selected":fallback_choice},
            "model_orchestration_gate":{"valid":selected is not None and allowed and
                                        completed["status"]=="COMPLETED" and cached is not None
                                        and fallback_choice is not None,"errors":[]}}
