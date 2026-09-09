from dataclasses import dataclass
class ChapterError(ValueError): pass
@dataclass(frozen=True)
class Chapter:
    chapter_id:str; title:str; start_page:int; end_page:int; order:int
def validate(chapters):
    ids=set(); last_end=0
    for c in chapters:
        if not c.chapter_id or c.chapter_id in ids or not c.title.strip() or c.start_page<1 or c.end_page<c.start_page or c.order<1: raise ChapterError("invalid chapter")
        if c.start_page<=last_end: raise ChapterError("overlap/order")
        ids.add(c.chapter_id); last_end=c.end_page
    return tuple(chapters)
