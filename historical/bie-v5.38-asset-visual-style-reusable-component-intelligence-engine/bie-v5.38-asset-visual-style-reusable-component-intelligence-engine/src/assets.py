def asset(asset_id,asset_type,uri=None,source_refs=None,
          semantic_tags=None,license_info=None):
    return {"asset_id":asset_id,"asset_type":asset_type,"uri":uri,
            "source_refs":source_refs or [],
            "semantic_tags":semantic_tags or [],
            "license_info":license_info}

def asset_types():
    return ["IMAGE","ICON","ILLUSTRATION","AUDIO","VIDEO","FONT",
            "MODEL","TEXTURE","DIAGRAM_COMPONENT","EQUATION_ASSET"]
