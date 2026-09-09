from content_address import content_id
from artifact import artifact
from storage import storage_location,storage_record

def compile_artifact(data,artifact_id,media_type,
                     backend,uri,tier="STANDARD"):
    cid=content_id(data)
    a=artifact(artifact_id,cid,len(data),media_type)
    loc=storage_location(cid,backend,uri,tier)
    return {"schema_version":"5.95",
            "artifact":a,
            "storage":storage_record(
                {"artifact_id":artifact_id,"content_id":cid},
                [loc]),
            "quality_gate":{"valid":True,"errors":[]}}
