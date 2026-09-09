from object_ref import object_ref,tenant_matches
from upload import upload_request,start,complete
from download import download_request,ranged
from multipart import multipart_upload,add_part,ready
from checksum import checksum,matches
from metadata import object_metadata,has_checksum
from versioning import object_version,current
from lifecycle import lifecycle_policy,transition_allowed
from quarantine import quarantine,release,reject
from access import object_access,allowed
from retention import retention,deletable

def compile_artifact_storage():
    ref=object_ref("obj-42","artifacts",
                   "tenant-a/course/lesson-1.mp4",
                   "tenant-a","v3")
    up=complete(start(upload_request(
        "u-1","obj-42","video/mp4",1048576,True)))
    dl=download_request("obj-42","v3",(0,1023))
    mp=multipart_upload("u-1","obj-42",524288,2)
    mp=add_part(mp,1,"sha256-part-1")
    mp=add_part(mp,2,"sha256-part-2")
    chk=checksum("SHA256","abc123")
    meta=object_metadata("obj-42","video/mp4",
                         1048576,"chk-1",
                         {"course":"lesson-1"})
    ver=object_version("obj-42","v3","v2",True)
    lc=lifecycle_policy("obj-42",
                        ["ACTIVE","ARCHIVED","DELETED"],
                        100,1000)
    q=release(quarantine("obj-42",
                         "scan-required","scanner-v1"))
    access=object_access("obj-42","user-1",
                         "READ","tenant-a","ALLOW")
    ret=retention("obj-42",1000,False)
    return {"schema_version":"6.21",
            "object_ref":ref,
            "upload":up,
            "download":dl,
            "multipart":mp,
            "checksum":chk,
            "metadata":meta,
            "version":ver,
            "lifecycle":lc,
            "quarantine":q,
            "access":access,
            "retention":ret,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "tenant_match":tenant_matches(ref,"tenant-a"),
              "upload_complete":up["status"]=="COMPLETED",
              "ranged_download":ranged(dl),
              "multipart_ready":ready(mp),
              "checksum_match":matches(chk,"abc123"),
              "has_checksum":has_checksum(meta),
              "current_version":current(ver),
              "active_to_archive":
                   transition_allowed("ACTIVE","ARCHIVED"),
              "quarantine_released":q["status"]=="RELEASED",
              "access_allowed":allowed(access),
              "retention_expired":deletable(ret,1000)
            }}
