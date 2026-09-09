import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from narration_quality import validate_narration
from visual_alignment import alignment,validate_alignment
from onscreen_text import text_overlay,validate_overlays
def test_m237():
 assert validate_narration("Explain electric charge.")["passed"]
 r=alignment({"segment_id":"s","concept_ids":["c"]},{"shot_id":"sh","concept_ids":["c"]})
 assert r["alignment"]==1
 assert validate_alignment([r])["passed"]
 assert validate_overlays([text_overlay("t","s","Key idea")])["passed"]
