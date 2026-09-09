import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from secret_ref import secret_ref,scoped
from key import key_metadata,usable
from key_rotation import rotation,activate_next
from certificate import certificate,valid_at
from revocation import revocation,is_revoked
from usage_policy import key_usage_policy,allows
from expiry import expiry_check,safe
from material_boundary import material_boundary,protected
from audit import secret_audit

def test_secret_key_rotation():
 s=secret_ref("s",1,"vault","a")
 assert scoped(s,"a")
 k=key_metadata("k",1,"AES","ENCRYPT","ACTIVE",0,10)
 assert usable(k,5)
 assert activate_next(rotation("k",1,2,5))["current_version"]==2

def test_certificate_revocation_policy():
 c=certificate("c","s","ca",0,10)
 assert valid_at(c,5)
 r=revocation("c","CERTIFICATE","x",6)
 assert is_revoked(r)
 p=key_usage_policy("k",["ENCRYPT"],["svc"])
 assert allows(p,"ENCRYPT","svc")
 assert not allows(p,"SIGN","svc")

def test_expiry_boundary_audit():
 e=expiry_check("k","KEY",10,10)
 assert not safe(e)
 b=material_boundary("k","KEY","HSM",False)
 assert protected(b)
 assert secret_audit("a","k","ROTATE","u","SUCCESS")["result"]=="SUCCESS"
