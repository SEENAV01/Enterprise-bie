def table_structure(table_id,headers=None,rows=None,
                    source_region=None):
    return {"table_id":table_id,"headers":headers or [],
            "rows":rows or [],"source_region":source_region}

def validate_table(table):
    width=len(table.get("headers",[]))
    bad=[r for r in table.get("rows",[]) if width and len(r)!=width]
    return {"valid":not bad,"bad_rows":len(bad)}
