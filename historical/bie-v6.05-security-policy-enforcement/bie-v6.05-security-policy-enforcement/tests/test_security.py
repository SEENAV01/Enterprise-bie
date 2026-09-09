import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from identity import identity
from auth import authentication_context,authenticated
from permission import permission
from rbac import role,role_allows
from authorize import authorization_request,decide
from tenant import isolated
from policy import security_policy
from privileged import privileged_operation,controls_required

def test_identity_auth():
 i=identity("u","t")
 a=authentication_context(i,1)
 assert authenticated(a)

def test_rbac_allow():
 p=permission("read","r")
 r=role("reader",[p])
 assert role_allows([r],"read","r")

def test_deny_default_and_tenant():
 req=authorization_request("u","t","write","r")
 assert decide(req,[],True)["decision"]=="DENY"
 assert decide(req,[role("r",[])],False)["reason"]=="TENANT_ISOLATION"
 assert not isolated("a","b")

def test_policy_privileged():
 assert security_policy("p",2)["default_effect"]=="DENY"
 op=privileged_operation("delete","x")
 assert "STEP_UP_AUTH" in controls_required(op)
