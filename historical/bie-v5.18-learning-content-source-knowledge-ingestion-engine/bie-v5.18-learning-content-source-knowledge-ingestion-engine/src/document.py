def document_record(document_id,source_id,title,pages=None):
    return {"document_id":document_id,"source_id":source_id,"title":title,
            "pages":pages or [],"structure":{},"elements":[]}
def page_record(page_id,page_number,text="",image_ref=None):
    return {"page_id":page_id,"page_number":page_number,"text":text,
            "image_ref":image_ref,"elements":[]}
