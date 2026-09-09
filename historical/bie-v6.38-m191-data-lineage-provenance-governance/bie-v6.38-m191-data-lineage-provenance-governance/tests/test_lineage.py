import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from dataset import dataset,active
from entity import entity,belongs_to
from lineage import lineage_edge,connects
from transformation import transformation,versioned
from provenance import provenance_claim,attributed
from ownership import ownership,assigned
from data_quality import quality_hook,passed
from governance import governance_rule,applies

def test_dataset_entity_lineage():
 d=dataset("d","data","owner")
 e=entity("e","ROW","d")
 l=lineage_edge("s","d")
 assert active(d) and belongs_to(e,"d")
 assert connects(l,"s","d")

def test_provenance_ownership_quality():
 assert versioned(transformation("t","JOIN","1"))
 assert attributed(provenance_claim("c","d","source"))
 assert assigned(ownership("d","owner"))
 assert passed(quality_hook("d","q","0.9",0.8),0.9)

def test_governance():
 assert applies(governance_rule("g","RESTRICTED","retain"),"RESTRICTED")
