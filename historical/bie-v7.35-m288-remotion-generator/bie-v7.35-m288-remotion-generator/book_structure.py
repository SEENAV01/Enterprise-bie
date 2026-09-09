import re
from collections import defaultdict

HEADING_RE = re.compile(r"^(chapter|unit|part|lesson|module)\s+[\w.-]+", re.I)
NUMBERED_RE = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s+(.+)$")

def heading_level(text):
    t = " ".join((text or "").split()).strip()
    if not t:
        return None
    m = NUMBERED_RE.match(t)
    if m:
        return min(6, m.group(1).count(".") + 1)
    if HEADING_RE.match(t):
        return 1
    return None

def is_toc_like(text):
    t = " ".join((text or "").split())
    return bool(re.search(r"\.{2,}\s*\d+$", t) or
                re.search(r"\b(page|pp?\.?)\s*\d+$", t, re.I))

def compile_sections(ir):
    """Build a deterministic hierarchical section tree from IR 2.x blocks."""
    nodes = []
    stack = []
    for page in ir.get("pages", []):
        for block in page.get("blocks", []):
            if block.get("kind") != "HEADING":
                continue
            title = " ".join((block.get("text") or "").split()).strip()
            if is_toc_like(title):
                continue
            level = heading_level(title) or 2
            node = {
                "section_id": block.get("block_id"),
                "title": title,
                "level": level,
                "start_page": page.get("page"),
                "source_block_id": block.get("block_id"),
                "children": [],
                "content_blocks": []
            }
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            if stack:
                stack[-1]["children"].append(node)
            else:
                nodes.append(node)
            stack.append(node)

    # Attach non-heading blocks to the deepest section on the same traversal.
    stack = []
    sections_by_id = {}

    def register(nodes):
        for n in nodes:
            sections_by_id[n["section_id"]] = n
            register(n["children"])
    register(nodes)

    for page in ir.get("pages", []):
        current = None
        for block in page.get("blocks", []):
            if block.get("kind") == "HEADING":
                sid = block.get("block_id")
                current = sections_by_id.get(sid, current)
            elif current and block.get("kind") != "FIGURE":
                current["content_blocks"].append(block.get("block_id"))

    return nodes

def flatten_sections(tree):
    out = []
    def walk(nodes, parent=None):
        for n in nodes:
            out.append({
                "section_id": n["section_id"],
                "parent_id": parent,
                "title": n["title"],
                "level": n["level"],
                "start_page": n["start_page"],
                "content_block_count": len(n["content_blocks"])
            })
            walk(n["children"], n["section_id"])
    walk(tree)
    return out

def chapter_units(tree):
    """Return top-level units suitable for downstream lesson planning."""
    return [{
        "unit_id": n["section_id"],
        "title": n["title"],
        "start_page": n["start_page"],
        "section_count": 1 + len(flatten_sections(n["children"]))
    } for n in tree]

def validate_structure(tree):
    errors = []
    seen = set()

    def walk(nodes, parent_level=0):
        for n in nodes:
            sid = n.get("section_id")
            if not sid:
                errors.append("section without section_id")
            elif sid in seen:
                errors.append(f"duplicate section_id: {sid}")
            seen.add(sid)
            if n.get("level", 0) <= parent_level:
                errors.append(f"invalid hierarchy at {sid}")
            walk(n.get("children", []), n.get("level", 0))
    walk(tree)
    return {"passed": not errors, "errors": errors}
