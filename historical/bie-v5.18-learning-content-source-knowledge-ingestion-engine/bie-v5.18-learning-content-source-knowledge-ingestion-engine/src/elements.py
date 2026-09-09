def equation_record(element_id,latex=None,alt_text=None):
    return {"element_id":element_id,"type":"EQUATION",
            "latex":latex,"alt_text":alt_text}
def table_record(element_id,rows,headers=None):
    return {"element_id":element_id,"type":"TABLE",
            "headers":headers or [],"rows":rows}
def figure_record(element_id,caption=None,asset_ref=None):
    return {"element_id":element_id,"type":"FIGURE",
            "caption":caption,"asset_ref":asset_ref}
