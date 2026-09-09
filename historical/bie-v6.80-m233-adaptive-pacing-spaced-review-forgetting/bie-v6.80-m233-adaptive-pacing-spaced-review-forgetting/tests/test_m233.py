import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from pacing import pace
from forgetting import retention
from spaced_review import next_review
def test_m233():
 assert pace({"a":0.5},20)["recommended_minutes"]==25
 assert retention(1,0)==1
 assert next_review(0.5,10)["next_review_day"]==11
