import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"engine"))
from structured_contract import validate_unit
from chunking import chunk_document
from long_book import batch_plan

def test_contract():
 u=json.loads((Path(__file__).parents[1]/"examples/sample-unit.json").read_text())
 ok,_=validate_unit(u)
 assert ok

def test_chunk_and_batch():
 pages=[{"page":1,"text":"a"*20},{"page":2,"text":"b"*20}]
 c=chunk_document(pages,max_chars=10)
 assert len(c)==4
 assert len(batch_plan(c,2))==2
