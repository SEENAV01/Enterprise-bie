from dataclasses import dataclass
class SectionError(ValueError): pass
@dataclass(frozen=True)
class Section:
    section_id:str; chapter_id:str; title:str; order:int; source_anchor:str
def validate(xs):
    seen=set(); bychapter={}
    for x in xs:
        if not x.section_id or x.section_id in seen or not x.chapter_id or not x.title.strip() or x.order<1 or not x.source_anchor: raise SectionError("invalid section")
        if x.order in bychapter.setdefault(x.chapter_id,set()): raise SectionError("duplicate order")
        bychapter[x.chapter_id].add(x.order); seen.add(x.section_id)
    return tuple(xs)
