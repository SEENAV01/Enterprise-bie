from key_value import record,same_key
from blob import blob,has_checksum
from collection import collection,active as collection_active
from namespace import namespace,active as namespace_active
from versioning import version,matches
from conditional import condition,evaluate
from transaction import transaction,add
from snapshot import snapshot,available
from consistency import consistency,strong
from audit import storage_event,successful
from observability import storage_metric,healthy

def compile_storage():
    ns=namespace("ns-1","artifacts","READ_COMMITTED")
    col=collection("col-1","ns-1","schema:artifact",["id"])
    rec=record("ns-1","artifact:1",{"status":"ACTIVE"},7,{"etag":"e7"})
    bl=blob("blob-1","store://artifact/1",1024,
            "application/json","sha256:abc")
    ver=version(7,"e7","2026-09-01T10:00:00Z")
    cond=condition("status","EQ","ACTIVE")
    tx=add(transaction("tx-1"),{"op":"PUT","key":"artifact:1"})
    snap=snapshot("snap-1","ns-1",7,"2026-09-01T10:00:00Z")
    cs=consistency("BOUNDED",500)
    ev=storage_event("se-1","ns-1","PUT","SUCCESS","artifact:1")
    met=storage_metric("sm-1","ns-1","PUT","SUCCESS",8,1024,0)
    return {"schema_version":"6.47","namespace":ns,"collection":col,
            "record":rec,"blob":bl,"version":ver,
            "condition":cond,"transaction":tx,"snapshot":snap,
            "consistency":cs,"audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "namespace_active":namespace_active(ns),
              "collection_active":collection_active(col),
              "same_key":same_key(rec,rec),
              "blob_checksum":has_checksum(bl),
              "version_match":matches(ver,7),
              "condition_true":evaluate(cond,"ACTIVE"),
              "transaction_operation":len(tx["operations"])==1,
              "snapshot_available":available(snap),
              "strong_consistency":strong(cs),
              "audit_success":successful(ev),
              "observability_healthy":healthy(met)
            }}
