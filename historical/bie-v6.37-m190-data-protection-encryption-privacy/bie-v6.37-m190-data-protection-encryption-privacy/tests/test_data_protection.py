import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from classification import classification,is_restricted
from encryption import encryption_policy,compliant
from masking import masking_policy,applies
from tokenization import tokenization_policy,protected
from retention import retention_policy,deletable
from privacy import privacy_policy,purpose_allowed
from data_handling import handling_policy,location_allowed
from access_boundary import access_boundary,action_allowed

def test_classification_encryption():
 c=classification("profile","RESTRICTED")
 assert is_restricted(c)
 e=encryption_policy(True,"AES-256-GCM")
 assert compliant(e,"AES-256-GCM")

def test_masking_tokenization():
 assert applies(masking_policy(["email"]),"email")
 assert protected(tokenization_policy(["id"],"vault"),"id")

def test_retention_privacy_handling_access():
 assert deletable(retention_policy("x","30d"))
 p=privacy_policy("analytics")
 assert purpose_allowed(p,"analytics")
 h=handling_policy("RESTRICTED",["IN"])
 assert location_allowed(h,"IN")
 a=access_boundary("u","RESTRICTED",["read"])
 assert action_allowed(a,"read")
