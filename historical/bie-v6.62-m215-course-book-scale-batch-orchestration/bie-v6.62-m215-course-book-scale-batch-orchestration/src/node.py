def node(i,t,source=None,deps=None,version="1"): return {"node_id":i,"node_type":t,"source_ref":source,"depends_on":deps or [],"version":version}
def valid(n): return bool(n["node_id"] and n["node_type"])
