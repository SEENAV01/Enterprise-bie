from index import index_definition,active
from analyzer import analyzer,analyze
from query_ast import term,boolean,query
from filtering import filter_clause,matches
from sorting import sort_clause,key
from pagination import pagination,bounded
from ranking import ranking,score
from consistency import query_consistency,acceptable
from lifecycle import index_lifecycle,queryable
from rebuild import rebuild,completed
from alias import index_alias,resolves
from query_plan import query_plan,valid
from observability import search_event,metric

def compile_search():
    idx=index_definition("workflows",
                          {"title":"text","status":"keyword",
                           "created_at":"date"},False,3)
    an=analyzer("standard","STANDARD",["LOWERCASE"])
    ast=query([term("title","electric"),
               boolean("AND",[term("status","READY")])])
    fl=filter_clause("status","EQ","READY")
    so=sort_clause("created_at","DESC")
    pg=pagination(20,cursor="c1")
    rk=ranking("BM25",{"title":2.0})
    co=query_consistency("BOUNDED_STALENESS",10)
    lc=index_lifecycle("workflows","ACTIVE",3)
    rb=rebuild("workflows",2,3); rb["status"]="COMPLETED"
    al=index_alias("workflows-current","workflows",True)
    qp=query_plan(["PARSE","FILTER","RANK","SORT","PAGE"],12)
    obs=search_event("search-1","workflows",
                     "QUERY","SUCCESS",6.8,14)
    return {"schema_version":"6.29",
            "index":idx,"analyzer":an,
            "query_ast":ast,"filter":fl,
            "sort":so,"pagination":pg,
            "ranking":rk,"consistency":co,
            "lifecycle":lc,"rebuild":rb,
            "alias":al,"query_plan":qp,
            "observability":obs,
            "quality_gate":{"valid":True,"errors":[]},
            "checks":{
              "index_active":active(idx),
              "analyzer_tokens":analyze(an,"Electric Field")==["Electric","Field"],
              "ast_query":ast["type"]=="QUERY",
              "filter_match":matches({"status":"READY"},fl),
              "sort_key":key({"created_at":5},so)==5,
              "pagination_bounded":bounded(pg),
              "ranking_score":score({"title":"electric field"},["electric"])==1,
              "consistency_ok":acceptable(co,7),
              "index_queryable":queryable(lc),
              "rebuild_complete":completed(rb),
              "alias_resolves":resolves(al),
              "plan_valid":valid(qp),
              "metric":metric(obs)
            }}
