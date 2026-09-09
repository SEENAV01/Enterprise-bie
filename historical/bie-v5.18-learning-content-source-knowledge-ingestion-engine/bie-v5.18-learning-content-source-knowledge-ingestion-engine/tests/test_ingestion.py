import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from ingest import ingest
from validation import validate_ingestion
def test_ingestion():
 r=ingest(
  {"source_id":"s","source_type":"PDF","title":"Book"},
  {"document_id":"d","source_id":"s","title":"Ch1"},
  [{"section_id":"x","title":"Intro","level":1}],
  [{"element_id":"p","text":"Hello world"}])
 assert r["schema_version"]=="5.18"
 assert validate_ingestion(r)["valid"]
