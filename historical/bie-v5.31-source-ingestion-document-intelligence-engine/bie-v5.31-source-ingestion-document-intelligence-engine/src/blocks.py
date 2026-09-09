def text_block(block_id,region_id,text,confidence=None):
    return {"block_id":block_id,"region_id":region_id,
            "block_type":"TEXT","text":text,"confidence":confidence}

def table_block(block_id,region_id,table_ref,confidence=None):
    return {"block_id":block_id,"region_id":region_id,
            "block_type":"TABLE","table_ref":table_ref,
            "confidence":confidence}

def figure_block(block_id,region_id,figure_ref,caption=None,
                 confidence=None):
    return {"block_id":block_id,"region_id":region_id,
            "block_type":"FIGURE","figure_ref":figure_ref,
            "caption":caption,"confidence":confidence}

def equation_block(block_id,region_id,formula,confidence=None):
    return {"block_id":block_id,"region_id":region_id,
            "block_type":"EQUATION","formula":formula,
            "confidence":confidence}
