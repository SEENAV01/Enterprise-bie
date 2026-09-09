def page(items,limit=50,cursor=None):
    limit=max(1,min(limit,1000))
    start=int(cursor) if cursor is not None else 0
    data=items[start:start+limit]
    nxt=str(start+limit) if start+limit<len(items) else None
    return {"items":data,"limit":limit,
            "next_cursor":nxt}

def has_next(result):
    return result.get("next_cursor") is not None
