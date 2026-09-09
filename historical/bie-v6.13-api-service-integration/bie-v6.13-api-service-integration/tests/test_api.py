import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from envelope import request_envelope,response_envelope
from api_contract import api_contract,valid
from schema_evolution import schema_version
from compatibility import compatibility_policy
from service import service,retire
from discovery import service_endpoint,endpoint_key
from health import health_status,is_available
from idempotent_api import idempotent_request,complete
from adapter import integration_adapter,adapter_ready
from contract_test import contract_test,pass_test

def test_envelopes_contract():
 r=request_envelope("r","s","op")
 assert r["request_id"]=="r"
 c=api_contract("s","op","GET","/x","Req","Res")
 assert valid(c)
 assert response_envelope("r",200)["request_id"]=="r"

def test_schema_service_discovery():
 assert schema_version("x",1)["version"]==1
 assert compatibility_policy("x","FULL")["mode"]=="FULL"
 assert retire(service("x","1"))["status"]=="RETIRED"
 assert endpoint_key(service_endpoint("x","a",1))==("x","a",1)

def test_health_idempotency_adapter_contract():
 assert is_available(health_status("x",True,True))
 req=idempotent_request("r","k","op")
 assert complete(req,{"ok":1})["status"]=="COMPLETED"
 assert adapter_ready(integration_adapter("a","p","HTTPS"))
 assert pass_test(contract_test("t",{},"c"))["status"]=="PASSED"
