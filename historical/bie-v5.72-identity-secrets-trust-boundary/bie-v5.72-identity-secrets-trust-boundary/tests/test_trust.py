import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import authorize_boundary
from policy import trust_policy
from credentials import credential_ref

def test_allowed_boundary():
 c=credential_ref("c",["RENDER"])
 r=authorize_boundary({"source_zone":"SANDBOX",
                       "target_zone":"WORKER",
                       "operation":"RENDER"},c,trust_policy())
 assert r["allowed"]

def test_denied_boundary():
 c=credential_ref("c",["RENDER"])
 r=authorize_boundary({"source_zone":"UNTRUSTED",
                       "target_zone":"PRODUCTION",
                       "operation":"RENDER"},c,trust_policy())
 assert not r["allowed"]
