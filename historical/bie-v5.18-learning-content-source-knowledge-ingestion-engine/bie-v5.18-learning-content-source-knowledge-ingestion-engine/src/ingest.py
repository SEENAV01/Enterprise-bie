from source import source_record
from document import document_record
from structure import build_hierarchy
from chunking import chunk_document
def ingest(source,document,sections=None,blocks=None):
    result={"schema_version":"5.18","source":source,
            "document":document}
    if sections is not None:
        result["hierarchy"]=build_hierarchy(sections)
    if blocks is not None:
        result["chunks"]=chunk_document(blocks)
    return result
