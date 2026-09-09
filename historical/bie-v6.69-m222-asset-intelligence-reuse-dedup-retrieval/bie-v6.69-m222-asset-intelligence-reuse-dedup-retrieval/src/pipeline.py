from asset import asset,valid
from index import AssetIndex
from dedup import DedupIndex
from retrieval import retrieve,score
from reuse import reuse_plan
from versioning import version_ref
from compatibility import compatible

def build_asset_intelligence():
    idx=AssetIndex(); dedup=DedupIndex()
    a1=asset("asset-field-001","diagram","asset://field.svg",
             {"subject":"electric field","style":"clean"},
             ["electric","field","diagram"],"sha256:field")
    a2=asset("asset-charge-001","animation","asset://charge.mp4",
             {"subject":"electric charge","style":"motion"},
             ["electric","charge","animation"],"sha256:charge")
    a3=asset("asset-field-duplicate","diagram","asset://field-copy.svg",
             {"subject":"electric field","style":"clean"},
             ["electric","field","diagram"],"sha256:field")
    for a in (a1,a2,a3): idx.add(a)
    duplicate_id,is_duplicate=dedup.register(a1)
    duplicate_id2,is_duplicate2=dedup.register(a3)
    found=retrieve(idx,"electric field diagram","diagram")
    ranked=[{"asset_id":a["asset_id"],"score":score(a,"electric field diagram")}
            for a in found]
    candidates=[dict(a,score=score(a,"electric field diagram")) for a in found
                if compatible(a,{"asset_type":"diagram"})]
    plan=reuse_plan({"asset_type":"diagram"},candidates)
    return {"schema_version":"6.69","asset_index_size":len(idx.all()),
            "assets":[a1,a2,a3],
            "deduplication":{"first":[duplicate_id,is_duplicate],
                             "duplicate":[duplicate_id2,is_duplicate2]},
            "retrieval":{"query":"electric field diagram",
                         "ranked":ranked},
            "reuse_plan":plan,
            "version_ref":version_ref(a1),
            "asset_gate":{"valid":(
                all(valid(a) for a in (a1,a2,a3))
                and is_duplicate2
                and plan["action"]=="REUSE"
                and compatible(a1,{"asset_type":"diagram"})
            ),"errors":[]}}
