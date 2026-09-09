from search_query import search_query,bounded
from index import index_definition,indexes_field
from filter import filter_expression,matches
from ranking import ranking_profile,score
from faceting import facet,count
from pagination import cursor,next_cursor
from consistency import retrieval_consistency,acceptable
from reindex import reindex,advance
from observability import query_event,metric

def compile_search():
    idx=index_definition("workflow-search",
                         ["title","status","tenant_id"],
                         "INVERTED",3)
    q=search_query("workflow-search",
                   "electric workflow",
                   {"status":"ACTIVE"},
                   ["status"],[("score","DESC")],20)
    filt=filter_expression("status","EQ","ACTIVE")
    rank=ranking_profile("default","BM25",
                         ["title"],{"title":2.0})
    fac=facet("status",10,"COUNT_DESC")
    pag=cursor(20)
    cons=retrieval_consistency("SESSION")
    job=advance(reindex("r-1","workflow-search",
                        2,3),100)
    event=query_event("search-1","workflow-search",
                      "q-1",8.4,17)
    return {"schema_version":"6.20",
            "index":idx,
            "query":q,
            "filter":filt,
            "ranking":rank,
            "facet":fac,
            "pagination":pag,
            "consistency":cons,
            "reindex":job,
            "observability":event,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "query_bounded":bounded(q),
              "indexes_status":indexes_field(idx,"status"),
              "filter_matches":matches(
                   filt,{"status":"ACTIVE"}),
              "ranking_score":score(
                   {"title":"electric workflow"},["electric"]),
              "facet_counts":count(
                   ["ACTIVE","ACTIVE","DONE"]),
              "next_cursor":next_cursor("key-20"),
              "consistency_acceptable":
                   acceptable(cons,{"EVENTUAL","SESSION","STRONG"}),
              "reindex_complete":job["status"]=="COMPLETE",
              "metric":metric(event)
            }}
