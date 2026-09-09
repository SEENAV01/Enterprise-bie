import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from secret_ref import secret_ref,active
from key import key_record,usable
from version import key_version,next_version
from rotation import rotation_plan,activate
from revocation import revocation,revoked
from lease import credential_lease
from envelope import envelope,valid
from retrieval import retrieval_request,fulfill

def test_secret_key_version():
 s=secret_ref("s",1)
 k=key_record("k","AES-256-GCM")
 assert active(s) and usable(k)
 assert key_version("k",1)["version"]==1
 assert next_version(1)==2

def test_rotation_revocation():
 r=activate(rotation_plan("k",1,2))
 assert r["status"]=="ACTIVE"
 assert revoked(revocation("k",1,"ROTATED"))

def test_lease_envelope_retrieval():
 assert credential_lease("c","p",1,2)["status"]=="ACTIVE"
 assert valid(envelope("k","dk","wk","AES-KW"))
 s=secret_ref("s",2)
 assert fulfill(retrieval_request(s,"p","test"),2)["status"]=="FULFILLED"
