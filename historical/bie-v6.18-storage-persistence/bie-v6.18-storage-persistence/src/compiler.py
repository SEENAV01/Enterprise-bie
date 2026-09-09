from entity import entity,has_field
from repository import repository,contract
from query import query
from transaction import transaction,commit
from index import index,covers
from migration import migration,applied
from archive import archive_policy,archival_due
from storage_lifecycle import lifecycle,valid_transition
from consistency import consistency_contract,compatible

def compile_storage():
    ent=entity("workflow",
               {"id":"string","tenant_id":"string",
                "status":"string","version":"int"},
               True,True)
    repo=repository("workflow-repo","workflow","STRONG")
    q=query("workflow",{"status":"ACTIVE"},[("version","DESC")],100)
    tx=commit(transaction("tx-1","SERIALIZABLE"))
    idx=index("workflow-status","workflow",
              ["tenant_id","status"],False)
    mig=applied(migration("m-1",1,2,
                           ["add:version","add:index"]))
    arch=archive_policy("workflow",100,1000,"COLD")
    lc=lifecycle("workflow")
    cc=consistency_contract("workflow","STRONG","STRONG")
    return {"schema_version":"6.18",
            "entity":ent,
            "repository":contract(repo),
            "query":q,
            "transaction":tx,
            "index":idx,
            "migration":mig,
            "archive_policy":arch,
            "lifecycle":lc,
            "consistency":cc,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "tenant_scoped":ent["tenant_scoped"],
              "has_version":has_field(ent,"version"),
              "index_covers":covers(
                  idx,["tenant_id","status"]),
              "archival_due":archival_due(arch,1000),
              "active_to_archive":valid_transition(
                  "ACTIVE","ARCHIVED"),
              "consistency":compatible(
                  cc,{"STRONG","EVENTUAL"})
            }}
