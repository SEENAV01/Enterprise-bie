import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from decomposer import decompose_book
def test_decompose():
 b={"chapters":[{"chapter_id":"c","sections":[{"section_id":"s","text":"x"}]}]}
 r=decompose_book(b,{"s":[{"dimension":"WHAT","text":"What is x?","source_span":"s"}]})
 assert r["schema_version"]=="4.4"
 assert r["validation"]["valid"]
