import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from auth_context import auth_context,authenticated
from token import token_contract,valid_at
from service_identity import service_identity,revoke
from policy import authorization_policy,allows
from enforcement import enforcement_point,enforce
from tenant import tenant_boundary,isolated
from rotation import rotation_hook,rotated
from security_event import security_event,denied
from credential import credential,expired

def test_auth_token_identity():
 a=auth_context("u","i")
 assert authenticated(a)
 t=token_contract("t","i","u",0,10)
 assert valid_at(t,5)
 assert not valid_at(t,10)
 assert revoke(service_identity("s","i"))["status"]=="REVOKED"

def test_authorization_enforcement():
 p=authorization_policy("r","READ",["u"],["read"])
 assert allows(p,"u","read")
 ep=enforcement_point("s","p",True)
 assert enforce(ep,"UNKNOWN")=="DENY"
 assert enforce(ep,"ALLOW")=="ALLOW"

def test_tenant_rotation_security():
 assert isolated(tenant_boundary("a","a"))
 assert not isolated(tenant_boundary("a","b"))
 assert rotated(rotation_hook("c",1,2,5))["status"]=="ROTATED"
 assert denied(security_event("e","AUTHZ","u","s","DENY"))
 assert expired(credential("c","SECRET",1,5),5)
