import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from principal import principal,active
from role import role
from permission import permission,matches
from scope import scope,matches as scope_matches
from authorization import authorize,allowed
from delegation import delegation
from service_identity import service_identity
from credential_boundary import credential_boundary,issuer_allowed,audience_allowed
from audit import audit_event

def test_identity_and_permission():
 p=principal("u","USER")
 perm=permission("read","r")
 assert active(p)
 assert matches(perm,"read","r")
 assert scope_matches(scope("r"),"r")

def test_authorization():
 p=principal("u","USER")
 perm=permission("read","r")
 assert allowed(authorize(p,[perm],"read","r"))
 assert authorize(p,[perm],"delete","r")["decision"]=="DENY"

def test_delegation_service_and_credentials():
 d=delegation("u","s",scope("*"))
 assert d["status"]=="ACTIVE"
 s=service_identity("s","aud")
 assert s["status"]=="ACTIVE"
 b=credential_boundary("s",["iss"],["aud"])
 assert issuer_allowed(b,"iss")
 assert audience_allowed(b,"aud")
 assert audit_event("e","u","read","r","ALLOW","MATCHED_PERMISSION")["decision"]=="ALLOW"
