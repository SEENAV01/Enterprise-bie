def search_query(index,
                text=None,
                filters=None,
                facets=None,
                sort=None,
                limit=20,
                cursor=None):
    return {"index":index,
            "text":text,
            "filters":filters or {},
            "facets":facets or [],
            "sort":sort or [],
            "limit":limit,
            "cursor":cursor}

def bounded(query,max_limit=100):
    return 1 <= query["limit"] <= max_limit
