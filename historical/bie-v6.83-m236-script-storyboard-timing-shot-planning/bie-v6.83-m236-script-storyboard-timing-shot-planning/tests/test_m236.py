import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from timing import estimate_duration
from sync import validate_sync
from shots import validate_shots
def test_m236():
 assert estimate_duration("one two three",130)>=3
 assert validate_sync([{"segment_id":"s","start":0,"end":3}])["passed"]
 assert validate_shots([{"segment_id":"s","start":0,"end":3}])["passed"]
