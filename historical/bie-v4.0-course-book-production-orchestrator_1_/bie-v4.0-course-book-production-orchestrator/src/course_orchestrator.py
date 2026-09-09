from global_memory import build_global_memory
from cross_chapter_graph import build_cross_chapter_graph
from asset_cache import build_asset_cache
from production_queue import build_production_queue

def prepare_book(book):
    memory=build_global_memory(book)
    graph=build_cross_chapter_graph(book.get("chapters",[]))
    cache=build_asset_cache(book.get("assets",[]))
    queue=build_production_queue(book.get("chapters",[]),graph)
    return {
      "schema_version":"4.0",
      "book_id":book.get("book_id"),
      "global_memory":memory,
      "dependency_graph":graph,
      "asset_cache":cache,
      "production_queue":queue,
      "policies":{
        "cross_chapter_consistency":True,
        "reuse_assets":True,
        "audio_driven_timing":True,
        "incremental_generation":True
      }
    }
