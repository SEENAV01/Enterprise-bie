def cursor(page_size,
           after=None,
           before=None):
    return {"page_size":page_size,
            "after":after,
            "before":before}

def next_cursor(last_sort_key):
    return {"after":last_sort_key}
