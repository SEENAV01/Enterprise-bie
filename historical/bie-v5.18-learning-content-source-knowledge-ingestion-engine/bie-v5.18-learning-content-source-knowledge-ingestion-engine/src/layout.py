def layout_element(element_id,element_type,bbox,content=None,
                   reading_order=0,page_id=None):
    return {"element_id":element_id,"element_type":element_type,
            "bbox":bbox,"content":content,"reading_order":reading_order,
            "page_id":page_id}
def sort_reading_order(elements):
    return sorted(elements,key=lambda x:(x.get("page_id",""),
                                         x.get("reading_order",0)))
