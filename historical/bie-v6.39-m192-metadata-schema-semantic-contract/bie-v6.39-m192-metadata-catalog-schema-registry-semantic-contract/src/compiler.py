from metadata import metadata,active as metadata_active
from schema import schema,active as schema_active
from version import schema_version,next_version
from compatibility import compatibility_rule,compatible
from semantic import semantic_type,matches
from field import field,required
from catalog import catalog_entry,indexed
from contract import semantic_contract,active as contract_active
from governance import schema_governance,approval_required
from audit import schema_event,successful
from observability import schema_metric,metric

def compile_catalog():
    meta=metadata("ds-1","customer-profile","Customer data",
                  "data-owner",{"domain":"customer"})
    f1=field("customer_id","string",True,"CustomerId")
    f2=field("email","string",False,"Email")
    sch=schema("sch-1","ds-1","1",[f1,f2],
               {"customer_id":"CustomerId","email":"Email"})
    sv=schema_version("sch-1","1","BACKWARD")
    cr=compatibility_rule("BACKWARD")
    sem=semantic_type("CustomerId","string","customer")
    cat=catalog_entry("ds-1","sch-1","meta-1","M191")
    con=semantic_contract("c-1","ds-1","1",
                          ["customer_id is unique"],
                          "producer-1",["consumer-a"])
    gov=schema_governance("sch-1","data-owner",True,"BACKWARD")
    ev=schema_event("se-1","ds-1","SCHEMA_PUBLISH","SUCCESS","schema-owner")
    met=schema_metric("sm-1","sch-1","1","SCHEMA_PUBLISH","SUCCESS")
    return {"schema_version":"6.39","metadata":meta,"schema":sch,
            "schema_version_record":sv,"compatibility":cr,
            "semantic_type":sem,"catalog":cat,
            "semantic_contract":con,"governance":gov,
            "audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "metadata_active":metadata_active(meta),
              "schema_active":schema_active(sch),
              "version_next":next_version("1")=="2",
              "compatible":compatible(cr,["customer_id"],["customer_id","email"]),
              "semantic_match":matches(sem,"CustomerId"),
              "required_field":required(f1),
              "catalog_indexed":indexed(cat),
              "contract_active":contract_active(con),
              "approval_required":approval_required(gov),
              "audit_success":successful(ev),
              "metric_complete":metric(met)["status"]=="SUCCESS"
            }}
