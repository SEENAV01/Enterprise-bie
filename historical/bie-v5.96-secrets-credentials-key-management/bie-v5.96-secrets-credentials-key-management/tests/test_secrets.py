import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from secret import secret_reference,redact
from scope import credential_scope,scope_allows
from grant import access_grant,expired,revoke
from rotation import rotation_policy,rotation_due
from injection import injection_request,injection_boundary

def test_reference_only():
 s=secret_reference("s1",version="2",service="api")
 assert s["reference_only"] and "value" not in s

def test_scope():
 s=credential_scope("sc","api",["read"],["r1"])
 assert scope_allows(s,"api","read","r1")
 assert not scope_allows(s,"api","write","r1")

def test_grant():
 g=access_grant("g",{"secret_id":"s"},{"scope_id":"x"},1,10,"w")
 assert expired(g,10)
 assert revoke(g)["status"]=="REVOKED"

def test_rotation():
 p=rotation_policy("s",10)
 assert rotation_due(0,10,p)

def test_injection():
 r=injection_boundary(injection_request("t","g","WORKER"))
 assert not r["payload_contains_raw_secret"]
