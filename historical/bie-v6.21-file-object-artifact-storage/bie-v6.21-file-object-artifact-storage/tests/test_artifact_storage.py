import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
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

def test_object_transfer():
 r=object_ref("o","b","k","t","v1")
 assert tenant_matches(r,"t")
 u=complete(start(upload_request("u","o","x",10)))
 assert u["status"]=="COMPLETED"
 assert ranged(download_request("o","v1",(0,9)))

def test_multipart_checksum_metadata():
 m=multipart_upload("u","o",10,2)
 m=add_part(m,1,"a"); m=add_part(m,2,"b")
 assert ready(m)
 c=checksum("SHA256","x")
 assert matches(c,"x")
 md=object_metadata("o","x",10,"c")
 assert has_checksum(md)

def test_version_lifecycle_quarantine_access_retention():
 v=object_version("o","v2","v1",True)
 assert current(v)
 assert transition_allowed("ACTIVE","ARCHIVED")
 q=release(quarantine("o","scan"))
 assert q["status"]=="RELEASED"
 a=object_access("o","u","READ","t","ALLOW")
 assert allowed(a)
 assert deletable(retention("o",10),10)
 assert not transition_allowed("DELETED","ACTIVE")
