def style_system(style_id,name,tokens=None,components=None):
    return {"style_id":style_id,"name":name,"tokens":tokens or {},
            "components":components or []}

def style_token(name,value,category):
    return {"name":name,"value":value,"category":category}
