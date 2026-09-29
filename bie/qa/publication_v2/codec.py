"""Closed-world request codec. No trust-store, signer or callback fields accepted."""
from .contracts import PublicationRequest,Lineage,OpenItem,strict_json,shape,seq
from ..release_v2.codec import bundle_from_dict,artifact_from_dict
from ..release_v2.contracts import canonical_bytes

def loads(data):
    d=strict_json(data)
    # Old requests remain readable, but cannot reach readiness without inventory.
    if 'inventory' not in d:d['inventory']=None
    shape(d,('schema_version','release_id','release_version','bundle','lineage','governance','open_items','inventory'))
    lines=[];items=[]
    for x in seq(d['lineage'],'lineage',2048):
        shape(x,('artifact_id','parent_ids'));lines.append(Lineage(x['artifact_id'],seq(x['parent_ids'],'parent_ids',2048)))
    for x in seq(d['open_items'],'open_items',2048):
        shape(x,('item_id','owner','code','artifact_ids'));items.append(OpenItem(x['item_id'],x['owner'],x['code'],seq(x['artifact_ids'],'artifact_ids',2048)))
    return PublicationRequest(d['schema_version'],d['release_id'],d['release_version'],bundle_from_dict(d['bundle']),tuple(lines),
        tuple(artifact_from_dict(x) for x in seq(d['governance'],'governance',3)),tuple(items),artifact_from_dict(d['inventory']) if d['inventory']is not None else None)

def dumps(request):return canonical_bytes(request.to_dict())
