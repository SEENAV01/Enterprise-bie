from dataclasses import dataclass
@dataclass(frozen=True)
class BridgeScope:
    target_concepts:tuple[str,...]; supporting_concepts:tuple[str,...]; excluded_concepts:tuple[str,...]; scope_reason:str
def scope_bridge_content(missing_concepts,dependency_map,available_concepts,max_support_depth=1):
    if max_support_depth<0: raise ValueError('depth')
    missing=tuple(dict.fromkeys(missing_concepts)); avail=set(available_concepts)
    if not missing or any(not x.strip() for x in missing) or any(x not in avail for x in missing): raise ValueError('missing concepts')
    support=set(); frontier=set(missing)
    for _ in range(max_support_depth):
        nxt=set()
        for c in sorted(frontier):
            for p in dependency_map.get(c,()):
                if p not in avail: raise ValueError('dependency unavailable')
                if p not in missing and p not in support: support.add(p); nxt.add(p)
        frontier=nxt
    included=set(missing)|support
    return BridgeScope(tuple(sorted(missing)),tuple(sorted(support)),tuple(sorted(avail-included)),'bounded prerequisite-only bridge scope')
