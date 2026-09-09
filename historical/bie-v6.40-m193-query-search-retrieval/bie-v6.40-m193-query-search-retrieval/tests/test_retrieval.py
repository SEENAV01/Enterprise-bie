import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from query import query,valid
from filter import predicate,matches
from sort import order,reverse
from pagination import page,has_cursor
from projection import projection,includes
from index import index,active
from consistency import consistency,strong
from result import result,complete

def test_query_filter_sort():
 q=query("r")
 assert valid(q)
 f=predicate("x","EQ",1)
 assert matches(f,1)
 assert reverse(order("x","DESC"))

def test_pagination_projection_index():
 assert has_cursor(page(10,"c"))
 assert includes(projection(["id"]),"id")
 assert active(index("r",["id"]))

def test_consistency_result():
 assert strong(consistency("STRONG"))
 assert complete(result([1],None,1,False))
