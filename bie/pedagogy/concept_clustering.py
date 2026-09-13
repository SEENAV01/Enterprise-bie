def cluster_concepts(mapping):
 out={}
 for c,tags in mapping.items():
  tags=sorted(set(tags))
  if not tags: raise ValueError("tags")
  out.setdefault(tags[0],[]).append(c)
 return tuple((k,tuple(sorted(v))) for k,v in sorted(out.items()))
