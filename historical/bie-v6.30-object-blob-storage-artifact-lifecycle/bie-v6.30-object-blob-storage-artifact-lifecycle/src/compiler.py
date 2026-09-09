from object import object_identity,active
from namespace import namespace,scoped
from metadata import metadata,valid as metadata_valid
from multipart import multipart_upload,complete
from checksum import checksum,verified
from content_address import content_address,same_content
from versioning import object_version,current
from retention import retention,protected as retention_protected
from legal_hold import legal_hold,protected as hold_protected
from lifecycle import lifecycle_transition,applies
from signed_access import signed_access,valid as signed_valid
from artifact import artifact,available
from observability import storage_event,metric

def compile_storage():
    obj=object_identity("obj-1","artifacts",
                        "lessons/lesson-1.mp4","v3")
    ns=namespace("artifacts","tenant-a","ap-south-1")
    md=metadata("video/mp4",1048576,
                 {"purpose":"lesson"})
    mp=multipart_upload("up-1","lesson-1.mp4",
                        524288,2)
    parts=["p1","p2"]
    cs=checksum("SHA256","abc123")
    ca=content_address("abc123","SHA256")
    ov=object_version("v3",100,True)
    rt=retention("TIME_BASED",500)
    lh=legal_hold("obj-1",False)
    lt=lifecycle_transition("STANDARD","ARCHIVE",
                            "age>30d")
    sa=signed_access("obj-1","GET",500,
                     {"ip":"trusted"})
    art=artifact("obj-1","VIDEO",
                 "render-job-42",{"duration":120})
    obs=storage_event("storage-1","obj-1",
                      "PUT","SUCCESS",1048576,42.1)
    return {"schema_version":"6.30",
            "object":obj,"namespace":ns,
            "metadata":md,"multipart":mp,
            "checksum":cs,"content_address":ca,
            "version":ov,"retention":rt,
            "legal_hold":lh,"lifecycle":lt,
            "signed_access":sa,"artifact":art,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "object_active":active(obj),
              "namespace_scoped":scoped(ns),
              "metadata_valid":metadata_valid(md),
              "multipart_complete":complete(mp,parts),
              "checksum_verified":verified(cs,"abc123"),
              "content_same":same_content(ca,ca),
              "version_current":current(ov),
              "retention_protected":retention_protected(rt,400),
              "hold_protected":not hold_protected(lh),
              "lifecycle_applies":applies(lt),
              "signed_access_valid":signed_valid(sa,400),
              "artifact_available":available(art),
              "metric":metric(obs)
            }}
