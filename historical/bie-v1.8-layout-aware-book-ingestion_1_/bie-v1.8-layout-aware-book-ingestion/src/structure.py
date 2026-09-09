def heading_level(text: str) -> int | None:
    t=text.strip()
    if t.startswith("###"): return 3
    if t.startswith("##"): return 2
    if t.startswith("#"): return 1
    return None

def build_heading_tree(pages):
    stack=[]
    nodes=[]
    for p in pages:
        for b in sorted(p["blocks"], key=lambda x:x.get("order",0)):
            if b.get("block_type")!="heading":
                continue
            level=b.get("level") or heading_level(b.get("text","")) or 1
            node={"id":b["block_id"],"title":b.get("text",""),"page":p["page"],"level":level,"children":[]}
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            if stack:
                stack[-1]["children"].append(node)
            else:
                nodes.append(node)
            stack.append(node)
    return nodes

def attach_parents(pages):
    # Assign each non-heading block to the nearest preceding heading on its page/order.
    for p in pages:
        current=None
        for b in sorted(p["blocks"], key=lambda x:x.get("order",0)):
            if b.get("block_type")=="heading":
                current=b["block_id"]
            elif current and not b.get("parent_id"):
                b["parent_id"]=current
    return pages
