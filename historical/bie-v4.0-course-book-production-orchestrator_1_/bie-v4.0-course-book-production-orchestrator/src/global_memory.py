def build_global_memory(book):
    terminology={}
    concepts={}
    style=book.get("style_profile",{})
    for item in book.get("terminology",[]):
        terminology[item["term"]]=item
    for c in book.get("concepts",[]):
        concepts[c["id"]]=c
    return {
      "book_id":book.get("book_id"),
      "terminology":terminology,
      "concepts":concepts,
      "style_profile":style,
      "version":"1.0"
    }
