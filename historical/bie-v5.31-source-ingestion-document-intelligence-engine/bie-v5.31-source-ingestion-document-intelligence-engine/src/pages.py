def page(page_id,document_id,page_number,width=None,height=None,
         image_ref=None,text_ref=None):
    return {"page_id":page_id,"document_id":document_id,
            "page_number":page_number,"width":width,"height":height,
            "image_ref":image_ref,"text_ref":text_ref}

def region(region_id,page_id,bbox,region_type,reading_order=None):
    return {"region_id":region_id,"page_id":page_id,"bbox":bbox,
            "region_type":region_type,"reading_order":reading_order}
