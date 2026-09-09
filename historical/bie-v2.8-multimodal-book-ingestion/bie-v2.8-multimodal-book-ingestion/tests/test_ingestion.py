import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from book_ingestion import ingest_book
def test_ingest():
 d=ingest_book([{"page_number":1,"text_blocks":[{"text":"Hello"}]}])
 assert d["schema_version"]=="2.8"
 assert len(d["evidence"])==1
 assert d["evidence"][0]["page_number"]==1
