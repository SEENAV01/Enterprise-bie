import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_source

def test_source():
 r=compile_source("d","book.pdf","application/pdf",
  [{"page_id":"p1"}],[{"region_id":"r1"}],
  [{"block_id":"b1"}],
  ocr_results=[{"region_id":"r1","confidence":0.95}])
 assert r["quality_gate"]["valid"]

def test_low_ocr():
 r=compile_source("d","scan.pdf","application/pdf",
  [],[],[],ocr_results=[{"region_id":"r1","confidence":0.5}])
 assert not r["quality_gate"]["valid"]
