import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from audit_event import audit_event
from integrity import integrity_metadata
from evidence import evidence,verify
from bundle import evidence_bundle,complete
from control import control,mapping
from attestation import attestation,accepted
from snapshot import compliance_snapshot,summary
from provenance import provenance,source_matches
from retention import evidence_retention,retention_expired

def test_audit_evidence():
 e=audit_event("e","TEST","u","r","read","ALLOW",1)
 assert e["outcome"]=="ALLOW"
 i=integrity_metadata("e",event_hash="h")
 v=evidence("ev","AUDIT","src",1,integrity=i)
 assert verify(v,"h")

def test_bundle_control():
 c=control("c","x","req")
 m=mapping(c["control_id"],["ev"],"PASS")
 b=complete(evidence_bundle("b","c",["ev"],"p","o"))
 assert m["status"]=="PASS" and b["status"]=="COMPLETE"

def test_attestation_snapshot():
 a=attestation("a","c","r","PASS",1)
 assert accepted(a)
 s=compliance_snapshot("s","p",[{"status":"PASS"},{"status":"FAIL"}],1)
 assert summary(s)=={"total":2,"pass":1,"fail":1,"review":0}

def test_provenance_retention():
 p=provenance("e","LOG","src","collector",1)
 assert source_matches(p,"src")
 r=evidence_retention("r",10)
 assert retention_expired(0,10,r)
