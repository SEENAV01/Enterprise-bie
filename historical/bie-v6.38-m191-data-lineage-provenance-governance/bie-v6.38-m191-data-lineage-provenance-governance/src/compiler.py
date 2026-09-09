from dataset import dataset,active
from entity import entity,belongs_to
from lineage import lineage_edge,connects
from transformation import transformation,versioned
from provenance import provenance_claim,attributed
from ownership import ownership,assigned
from data_quality import quality_hook,passed
from governance import governance_rule,applies
from audit import governance_event,successful
from observability import lineage_metric,metric

def compile_governance():
    ds=dataset("ds-1","customer-profile","data-owner","RESTRICTED")
    ent=entity("ent-1","CUSTOMER","ds-1")
    edge=lineage_edge("raw-customers","ds-1","normalize-v2")
    tr=transformation("normalize-v2","NORMALIZE","2","pipeline-1")
    prov=provenance_claim("pc-1","ds-1","source-system",
                          "ingestion",1000,0.99)
    own=ownership("ds-1","data-owner","data-steward","customer")
    q=quality_hook("ds-1","completeness","0.99",0.95)
    gr=governance_rule("g-1","RESTRICTED","document-lineage","HIGH")
    ev=governance_event("ge-1","ds-1","LINEAGE_UPDATE","SUCCESS","pipeline-1")
    met=lineage_metric("lm-1","ds-1","LINEAGE_UPDATE","SUCCESS",1)
    return {"schema_version":"6.38","dataset":ds,"entity":ent,
            "lineage":edge,"transformation":tr,
            "provenance":prov,"ownership":own,"quality":q,
            "governance":gr,"audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "dataset_active":active(ds),
              "entity_belongs":belongs_to(ent,"ds-1"),
              "lineage_connected":connects(edge,"raw-customers","ds-1"),
              "transformation_versioned":versioned(tr),
              "provenance_attributed":attributed(prov),
              "ownership_assigned":assigned(own),
              "quality_passed":passed(q,0.99),
              "governance_applies":applies(gr,"RESTRICTED"),
              "audit_success":successful(ev),
              "metric_complete":metric(met)["edge_count"]==1
            }}
