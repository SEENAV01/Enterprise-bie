def segment_book(book):
    segments=[]
    for chapter in book.get("chapters",[]):
        for section in chapter.get("sections",[]):
            text=section.get("text","")
            segments.append({
              "segment_id":section["section_id"],
              "chapter_id":chapter["chapter_id"],
              "heading":section.get("heading",""),
              "text":text,
              "page_start":section.get("page_start"),
              "page_end":section.get("page_end")
            })
    return segments
