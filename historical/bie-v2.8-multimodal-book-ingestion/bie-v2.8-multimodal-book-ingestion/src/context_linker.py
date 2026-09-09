def link_page_context(page):
    # Preserve page-local relationships before global knowledge extraction.
    links=[]
    assets=page.get("images",[])+page.get("tables",[])+page.get("equations",[])
    for asset in assets:
        links.append({
            "page_id":page["page_id"],
            "asset_ref":asset.get("asset_id"),
            "nearby_text_refs":[x["block_id"] for x in page.get("text_blocks",[])],
            "relation":"PAGE_CONTEXT"
        })
    return links

def link_adjacent_pages(previous_page, current_page):
    if not previous_page: return []
    return [{
        "source_page":previous_page["page_number"],
        "target_page":current_page["page_number"],
        "relation":"ADJACENT_CONTEXT"
    }]
