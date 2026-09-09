from config import config,validate
from overlay import overlay,resolve
from flag import feature_flag
from policy import dynamic_policy

def compile_runtime_config(key,value,value_type,
                           environment="production",
                           flag_id=None):
    cfg=config(key,value,value_type,
               source=environment)
    flag=feature_flag(flag_id,True,100) if flag_id else None
    policy=dynamic_policy("runtime-default",1,{key:value})
    return {"schema_version":"5.99",
            "config":cfg,
            "valid":validate(cfg),
            "overlay":overlay(environment,{key:value}),
            "effective":resolve(
                [overlay(environment,{key:value})]),
            "feature_flag":flag,
            "policy":policy,
            "quality_gate":{"valid":validate(cfg),"errors":[]}}
