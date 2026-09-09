from query import query,valid
from filter import predicate,matches
from sort import order,reverse
from pagination import page,has_cursor
from projection import projection,includes
from index import index,active
from consistency import consistency,strong
from result import result,complete
from audit import retrieval_event,successful
from observability import retrieval_metric,healthy

def compile_retrieval():
    f=predicate("status","EQ","ACTIVE")
    s=order("created_at","DESC")
    pg=page(25,"cursor-1")
    pr=projection(["id","status","created_at"])
    ix=index("artifacts",["status","created_at"])
    cs=consistency("BOUNDED",500)
    q=query("artifacts",[f],[*pr["fields"]],[s],pg,cs)
    res=result([{"id":"a-1","status":"ACTIVE"}],"cursor-2",1,False)
    ev=retrieval_event("qr-1","user-1","artifacts","QUERY","SUCCESS")
    met=retrieval_metric("qm-1","artifacts",18,1,"SUCCESS")
    return {"schema_version":"6.40","query":q,"filter":f,
            "sort":s,"pagination":pg,"projection":pr,
            "index":ix,"consistency":cs,"result":res,
            "audit":ev,"observability":met,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "query_valid":valid(q),
              "filter_matches":matches(f,"ACTIVE"),
              "descending":reverse(s),
              "cursor_pagination":has_cursor(pg),
              "projection_includes":includes(pr,"id"),
              "index_active":active(ix),
              "bounded_consistency":not strong(cs),
              "result_complete":complete(res),
              "audit_success":successful(ev),
              "observability_healthy":healthy(met)
            }}
