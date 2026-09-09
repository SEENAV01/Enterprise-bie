import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from source_adapter import ingest_source, build_document_ir

def test_text_source_creates_document_ir(tmp_path):
    p = tmp_path / "book.txt"
    p.write_text("Electric charge is a property of matter.", encoding="utf-8")
    source = ingest_source(p)
    ir = build_document_ir(source)
    assert source["status"] == "INGESTED"
    assert ir["block_count"] == 1
    assert ir["requires_ocr"] is False
    assert ir["blocks"][0]["locator"]["source"] == "book.txt"

def test_unsupported_source_is_explicit(tmp_path):
    p = tmp_path / "book.docx"
    p.write_bytes(b"not supported")
    try:
        ingest_source(p)
    except ValueError as e:
        assert "Unsupported source type" in str(e)
    else:
        raise AssertionError("unsupported input must fail explicitly")
