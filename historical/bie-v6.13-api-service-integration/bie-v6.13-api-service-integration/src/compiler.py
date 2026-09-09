from envelope import request_envelope,response_envelope
from api_contract import api_contract
from schema_evolution import schema_version
from compatibility import compatibility_policy
from service import service
from discovery import service_endpoint
from health import health_status
from idempotent_api import idempotent_request,complete
from adapter import integration_adapter
from contract_test import contract_test,pass_test

def compile_api():
    req=request_envelope("req-1","workflow",
                         "start","tenant-a","idem-1")
    res=response_envelope("req-1",200,{"workflow_id":"wf-1"})
    api=api_contract("workflow","start","POST",
                     "/v1/workflows","WorkflowStart",
                     "WorkflowResponse","1")
    sv=schema_version("WorkflowStart",1,"BACKWARD")
    cp=compatibility_policy("workflow-api","BACKWARD")
    svc=service("workflow","1","/v1","platform")
    ep=service_endpoint("workflow","workflow.internal",8080)
    health=health_status("workflow",True,True,["state-store"])
    idem=complete(idempotent_request(
        "req-1","idem-1","start"),res)
    ad=integration_adapter("payments",
                           "payment-provider","HTTPS",30,True)
    ct=pass_test(contract_test("workflow-start",
                               api,"workflow-client",200))
    return {"schema_version":"6.13",
            "request_envelope":req,
            "response_envelope":res,
            "api_contract":api,
            "schema_version_contract":sv,
            "compatibility":cp,
            "service":svc,
            "endpoint":ep,
            "health":health,
            "idempotent_api":idem,
            "integration_adapter":ad,
            "contract_test":ct,
            "quality_gate":{"valid":True,"errors":[]}}
