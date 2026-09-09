from page_parser import parse_page
from evidence import build_page_evidence
from context_linker import link_page_context,link_adjacent_pages

def ingest_book(raw_pages):
    pages=[]
    evidence=[]
    context_links=[]
    prev=None
    for p in raw_pages:
        page=parse_page(
            p["page_number"],p.get("text_blocks"),
            p.get("images"),p.get("tables"),p.get("equations")
        )
        pages.append(page)
        evidence += build_page_evidence(page)
        context_links += link_page_context(page)
        context_links += link_adjacent_pages(prev,page)
        prev=page
    return {
        "schema_version":"2.8",
        "pages":pages,
        "evidence":evidence,
        "context_links":context_links
    }
