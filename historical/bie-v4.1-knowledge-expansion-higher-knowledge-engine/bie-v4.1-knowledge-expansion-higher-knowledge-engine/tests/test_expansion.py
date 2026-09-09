import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from knowledge_expansion import expand
def test_expand():
 r=expand(["ohms_law"],[{"id":"x","title":"Higher","relation":"extends","content":"X","depends_on":["ohms_law"]}],["ohms_law"],[])
 assert r["schema_version"]=="4.1"
 assert r["items"][0]["classification"]=="HIGHER_KNOWLEDGE"
 assert len(r["verification_requests"])==1
