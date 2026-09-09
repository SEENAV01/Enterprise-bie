from lease import lease,valid
from fencing import fencing_token,permits
from mutex import mutex,acquirable
from leader import leadership,is_leader
from quorum import quorum,reached
from epoch import ownership_epoch,newer
from failure import failure_detector,suspected
from coordination import coordination_request,complete
from observability import coordination_event,metric

def compile_coordination():
    l=lease("workflow:42","worker-1",500,7)
    f=fencing_token("workflow:42",7)
    m=mutex("workflow:42")
    leader=leadership("workflow-workers","worker-1",12)
    q=quorum(5,3)
    old=ownership_epoch("workflow:42",6,"worker-0")
    new=ownership_epoch("workflow:42",7,"worker-1")
    fd=failure_detector("worker-0",100,30)
    req=complete(coordination_request(
        "coord-1","workflow:42","ACQUIRE","worker-1"))
    obs=coordination_event("coord-event",
                           "workflow:42","ACQUIRE",
                           "GRANTED","worker-1",7,3.1)
    return {"schema_version":"6.24",
            "lease":l,"fencing_token":f,
            "mutex":m,"leadership":leader,
            "quorum":q,"ownership_epoch":new,
            "failure_detector":fd,
            "coordination_request":req,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "lease_valid":valid(l,400),
              "fence_permitted":permits(f,7),
              "mutex_acquirable":acquirable(m),
              "is_leader":is_leader(leader,"worker-1"),
              "quorum_reached":reached(q,3),
              "epoch_newer":newer(new,old),
              "node_suspected":suspected(fd,130),
              "request_completed":
                   req["status"]=="COMPLETED",
              "metric":metric(obs)
            }}
