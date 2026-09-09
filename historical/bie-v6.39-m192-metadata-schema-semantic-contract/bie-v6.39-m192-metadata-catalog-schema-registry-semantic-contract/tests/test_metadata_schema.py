import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from metadata import metadata,active
from schema import schema
from version import schema_version,next_version
from compatibility import compatibility_rule,compatible
from semantic import semantic_type,matches
from field import field,required
from catalog import catalog_entry,indexed
from contract import semantic_contract
from governance import schema_governance,approval_required

def test_metadata_schema_version():
 m=metadata("d","data")
 s=schema("s","d","1")
 assert active(m) and s["status"]=="ACTIVE"
 assert schema_version("s","1")["version"]=="1"
 assert next_version("1")=="2"

def test_compatibility_semantics_fields():
 r=compatibility_rule("BACKWARD")
 assert compatible(r,["id"],["id","name"])
 sem=semantic_type("CustomerId","string")
 assert matches(sem,"CustomerId")
 assert required(field("id","string",True))

def test_catalog_contract_governance():
 assert indexed(catalog_entry("d","s","m","l"))
 assert semantic_contract("c","d","1")["status"]=="ACTIVE"
 assert approval_required(schema_governance("s","owner"))
