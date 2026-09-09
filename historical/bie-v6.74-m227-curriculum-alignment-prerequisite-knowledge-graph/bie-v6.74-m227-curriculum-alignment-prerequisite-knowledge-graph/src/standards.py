def standard(standard_id,title,description=None,framework=None):
    return {"standard_id":standard_id,"title":title,
            "description":description,"framework":framework}
def valid_standard(s):
    return bool(s.get("standard_id") and s.get("title"))
