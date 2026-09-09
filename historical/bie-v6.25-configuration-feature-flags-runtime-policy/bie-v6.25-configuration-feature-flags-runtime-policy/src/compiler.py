from config import config_value,typed
from scope import scope,hierarchy
from defaults import default,resolve
from validation import rule,validate
from secret_ref import secret_ref,is_reference
from reload import reload_policy,hot_reload
from feature_flag import feature_flag,enabled
from rollout import rollout,applies
from policy import policy,evaluate
from observability import config_event,metric

def compile_runtime_policy():
    cfg=config_value("video.max_resolution","1080p",
                     "string","ENV","WORKFLOW")
    scopes=hierarchy([
        scope("GLOBAL",None,0),
        scope("TENANT","GLOBAL",10),
        scope("WORKFLOW","TENANT",20)])
    d=default("timeout_seconds",300,"integer")
    r=rule("timeout_seconds",True,None,1,3600)
    sr=secret_ref("storage.api_key","SECRET_STORE","v3")
    rp=reload_policy("ON_CHANGE",False)
    ff=feature_flag("new_renderer",False,"renderer rollout")
    ro=rollout("new_renderer","PERCENTAGE",25)
    p=policy("production-renderers","ALLOW",
             {"environment":"production"},5)
    obs=config_event("cfg-1","video.max_resolution",
                     "RESOLVE","APPLIED","WORKFLOW","ENV")
    return {"schema_version":"6.25",
            "config":cfg,"scopes":scopes,
            "default":d,"validation":r,
            "secret_ref":sr,"reload":rp,
            "feature_flag":ff,"rollout":ro,
            "policy":p,"observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "typed":typed(cfg),
              "scope_priority":scopes[0]["priority"]==20,
              "default_resolved":resolve(None,300)==300,
              "validation":validate(300,r),
              "secret_is_reference":is_reference(sr),
              "hot_reload":hot_reload(rp),
              "flag_enabled":enabled(ff,True),
              "rollout_applies":applies(ro,10),
              "policy_allows":evaluate(p,{"environment":"production"}),
              "metric":metric(obs)
            }}
