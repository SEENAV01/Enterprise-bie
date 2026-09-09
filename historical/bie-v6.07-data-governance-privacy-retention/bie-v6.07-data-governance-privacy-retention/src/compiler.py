from classification import classification
from privacy import privacy_label
from retention import retention_policy
from lineage import lineage
from residency import residency
from deletion import deletion_request
from tenant import tenant_data

def compile_governance(resource_id,tenant_id):
    c=classification("CONFIDENTIAL",tenant_id)
    p=privacy_label("GENERAL",False,False)
    r=retention_policy("default",2592000,"DELETE")
    l=lineage(resource_id)
    res=residency(resource_id,["IN"],"IN")
    d=deletion_request(resource_id,0)
    t=tenant_data(resource_id,tenant_id)
    return {"schema_version":"6.07",
            "classification":c,"privacy":p,
            "retention":r,"lineage":l,
            "residency":res,"deletion":d,
            "tenant":t,
            "quality_gate":{"valid":True,"errors":[]}}
