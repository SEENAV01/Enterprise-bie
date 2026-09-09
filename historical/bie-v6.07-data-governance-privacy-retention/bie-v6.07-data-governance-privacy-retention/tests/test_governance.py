import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from classification import classification,at_least
from privacy import privacy_label,requires_protection
from retention import retention_policy,expired
from hold import hold,active
from lineage import lineage,add_parent
from residency import residency,compliant
from deletion import deletion_request,evaluate
from tenant import tenant_data,same_tenant

def test_classification_privacy():
 c=classification("RESTRICTED")
 assert at_least(c,"CONFIDENTIAL")
 assert requires_protection(privacy_label("PII",True))

def test_retention_hold():
 r=retention_policy("r",10)
 assert expired(0,10,r)
 h=hold("h","x","legal",1,20)
 assert active(h,5)

def test_lineage_residency():
 l=add_parent(lineage("x"),"p")
 assert "p" in l["parents"]
 assert compliant(residency("x",["IN"],"IN"))

def test_deletion_tenant():
 q=evaluate(deletion_request("x",0),True,False)
 assert q["status"]=="APPROVED"
 assert same_tenant(tenant_data("x","t"),"t")
