def reading_order(regions):
    return sorted(regions,key=lambda r:
                  (r.get("reading_order") is None,
                   r.get("reading_order",0),
                   r.get("bbox",[0,0,0,0])[1],
                   r.get("bbox",[0,0,0,0])[0]))

def layout_record(page_id,regions):
    ordered=reading_order(regions)
    return {"page_id":page_id,"regions":ordered}
