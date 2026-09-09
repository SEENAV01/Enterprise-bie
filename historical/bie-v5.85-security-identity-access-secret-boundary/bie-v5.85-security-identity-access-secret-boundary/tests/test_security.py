import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from identity import principal
from authn import auth_context
from authorize import authorized
from policy import access_policy
from secrets import secret_ref,validate_secret_ref

def test_allow():
 p=principal("u","USER",roles=["EDITOR"],active=True)
 c=auth_context("u","SESSION")
 pol=access_policy("ARTIFACT","READ",["EDITOR"],effect="ALLOW")
 assert authorized(c,p,{"type":"ARTIFACT","scope":"x"},pol)

def test_deny_inactive():
 p=principal("u","USER",roles=["EDITOR"],active=False)
 c=auth_context("u","SESSION")
 pol=access_policy("ARTIFACT","READ",["EDITOR"],effect="ALLOW")
 assert not authorized(c,p,{"type":"ARTIFACT","scope":"x"},pol)

def test_secret_ref():
 assert validate_secret_ref(secret_ref("api-key"))

