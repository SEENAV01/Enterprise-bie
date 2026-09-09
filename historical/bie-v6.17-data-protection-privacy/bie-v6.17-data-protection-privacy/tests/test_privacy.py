import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from classification import classification,is_restricted
from encryption import encryption_policy,protected
from field_protection import field_protection,protects
from redaction import redaction,redact
from retention import retention_policy,deletable
from deletion import deletion_request,approve,complete
from privacy_boundary import privacy_boundary,purpose_allowed
from access_audit import protected_access,allowed
from masking import masking_policy,apply

def test_classification_encryption_fields():
 c=classification("d","RESTRICTED")
 assert is_restricted(c)
 e=encryption_policy("d","AES","key://d")
 assert protected(e)
 f=field_protection("d",["email"])
 assert protects(f,"email")
 assert redact(redaction("d",["ssn"]),
               {"ssn":"123"})["ssn"]=="[REDACTED]"

def test_retention_deletion_privacy():
 r=retention_policy("d",10)
 assert deletable(r,10)
 d=complete(approve(deletion_request("x","d","u")))
 assert d["status"]=="COMPLETED"
 p=privacy_boundary("d","t",["support"])
 assert purpose_allowed(p,"support")
 a=protected_access("a","u","d","support","ALLOW","t")
 assert allowed(a)

def test_masking():
 m=masking_policy("d",["phone"],4)
 assert apply(m,{"phone":"1234567890"})["phone"]=="******7890"
