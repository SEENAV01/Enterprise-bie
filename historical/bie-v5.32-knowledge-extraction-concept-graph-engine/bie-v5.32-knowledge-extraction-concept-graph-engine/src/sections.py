def section(section_id,title,order,parent_id=None,source_refs=None):
    return {"section_id":section_id,"title":title,"order":order,
            "parent_id":parent_id,"source_refs":source_refs or []}
