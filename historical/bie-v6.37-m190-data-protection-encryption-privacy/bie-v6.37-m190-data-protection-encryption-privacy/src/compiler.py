from classification import classification,is_restricted
from encryption import encryption_policy,compliant
from masking import masking_policy,applies
from tokenization import tokenization_policy,protected
from retention import retention_policy,deletable
from privacy import privacy_policy,purpose_allowed
from data_handling import handling_policy,location_allowed
from access_boundary import access_boundary,action_allowed
from audit import protection_event,successful
from observability import protection_metric,metric

def compile_protection():
    c=classification("customer_profile","RESTRICTED",["PII"])
    e=encryption_policy(True,"AES-256-GCM",True,True)
    m=masking_policy(["email","phone"],"PARTIAL")
    t=tokenization_policy(["customer_id"],"vault-1",True)
    r=retention_policy("customer_profile","365d","ANONYMIZE",False)
    p=privacy_policy("service_delivery","CONTRACT",True,False)
    h=handling_policy("RESTRICTED",["IN"],["processor-a"])
    a=access_boundary("service-1","RESTRICTED",["read","mask"])
    ev=protection_event("dp-1","service-1","customer_profile",
                        "ENCRYPT","SUCCESS")
    met=protection_metric("dp-1","customer_profile","RESTRICTED",
                           "ENCRYPT","SUCCESS")
    return {"schema_version":"6.37","classification":c,
            "encryption":e,"masking":m,"tokenization":t,
            "retention":r,"privacy":p,"handling":h,
            "access_boundary":a,"audit":ev,
            "observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "restricted":is_restricted(c),
              "encryption_compliant":compliant(e,"AES-256-GCM"),
              "masking_applies":applies(m,"email"),
              "tokenization_protected":protected(t,"customer_id"),
              "retention_deletable":deletable(r),
              "purpose_allowed":purpose_allowed(p,"service_delivery"),
              "location_allowed":location_allowed(h,"IN"),
              "action_allowed":action_allowed(a,"mask"),
              "audit_success":successful(ev),
              "metric_complete":metric(met)["status"]=="SUCCESS"
            }}
