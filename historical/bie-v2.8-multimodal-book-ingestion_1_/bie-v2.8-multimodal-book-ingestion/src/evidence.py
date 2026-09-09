def evidence_record(page, block, modality="text", asset_ref=None):
    return {
        "evidence_id":f'{page["page_id"]}:{block.get("block_id","asset")}',
        "page_id":page["page_id"],
        "page_number":page["page_number"],
        "modality":modality,
        "content":block.get("text") or block.get("description") or "",
        "asset_ref":asset_ref,
        "provenance":{
            "source":"BOOK",
            "page":page["page_number"],
            "locator":block.get("block_id")
        }
    }

def build_page_evidence(page):
    out=[]
    for b in page.get("text_blocks",[]):
        out.append(evidence_record(page,b,"text"))
    for a in page.get("images",[]):
        out.append(evidence_record(page,a,"image",a.get("asset_id")))
    for t in page.get("tables",[]):
        out.append(evidence_record(page,t,"table",t.get("asset_id")))
    for e in page.get("equations",[]):
        out.append(evidence_record(page,e,"equation",e.get("asset_id")))
    return out
