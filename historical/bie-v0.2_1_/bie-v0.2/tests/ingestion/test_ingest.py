from pathlib import Path
from backend.ingestion.ingest import classify_block

def test_classify_paragraph():
    assert classify_block('This is ordinary text.') == 'paragraph'

def test_classify_heading():
    assert classify_block('Chapter 1', font_size=18, bold=True) == 'heading_candidate'

def test_classify_equation():
    assert classify_block('E = kQ/r^2') == 'equation_candidate'
