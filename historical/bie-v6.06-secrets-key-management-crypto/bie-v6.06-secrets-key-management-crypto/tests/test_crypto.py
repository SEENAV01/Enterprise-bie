import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from secret import secret_reference
from key import key_reference,key_active
from lifecycle import lifecycle,usable
from rotation import rotation_plan,complete_rotation
from access import access_policy,allowed
from redaction import redact
from revocation import revocation,revoked

def test_reference_and_lifecycle():
 s=secret_reference("s",2,"worker")
 k=key_reference("k",2,"SIGN","Ed25519")
 assert s["version"]==2
 assert key_active(k)
 assert usable(lifecycle("s","ACTIVE",2,1))

def test_rotation_access():
 p=rotation_plan("s",1,2,1)
 assert complete_rotation(p)["current_version"]==2
 a=access_policy("s",["worker"],["READ"],"ALLOW")
 assert allowed(a,"worker","READ")

def test_redaction_revocation():
 assert redact({"token":"x","ok":1})["token"]=="[REDACTED]"
 assert revoked(revocation("k",1,2,"retired"))
