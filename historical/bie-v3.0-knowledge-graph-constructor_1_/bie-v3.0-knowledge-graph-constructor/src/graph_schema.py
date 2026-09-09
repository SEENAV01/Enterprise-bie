NODE_TYPES=[
"concept","definition","law","principle","process","procedure","example",
"derivation","question","application","condition","quantity","entity",
"prerequisite","chapter","section"
]
EDGE_TYPES=[
"defines","explains","causes","requires","part_of","precedes","derives",
"applies_to","example_of","contrasts_with","depends_on","answers","measures",
"contains","supports"
]

def node(node_id,node_type,name,evidence=None,source_scope="BOOK",confidence=1.0,metadata=None):
    return {
      "id":node_id,"type":node_type,"name":name,
      "source_scope":source_scope,"confidence":confidence,
      "evidence_ids":evidence or [],"metadata":metadata or {}
    }

def edge(source,target,relation,evidence=None,source_scope="BOOK",confidence=1.0):
    return {
      "source":source,"target":target,"relation":relation,
      "source_scope":source_scope,"confidence":confidence,
      "evidence_ids":evidence or []
    }
