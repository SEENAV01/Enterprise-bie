NODE_TYPES=[
"CONCEPT","CLAIM","DEFINITION","PROCESS","CAUSE","APPLICATION",
"EXAMPLE","PREREQUISITE","HIGHER_KNOWLEDGE","SOURCE"
]
EDGE_TYPES=[
"DEFINES","SUPPORTS","CONTRADICTS","DEPENDS_ON","CAUSES","APPLIES_TO",
"EXAMPLE_OF","EXTENDS","GENERALIZES","SOURCED_BY","RELATED_TO"
]
def node(node_id,node_type,label,properties=None):
    return {"id":node_id,"type":node_type,"label":label,
            "properties":properties or {}}
def edge(source,target,edge_type,properties=None):
    return {"source":source,"target":target,"type":edge_type,
            "properties":properties or {}}
