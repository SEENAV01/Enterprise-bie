import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from quality_score import quality_score,classify
from perceptual import perceptual_similarity,above_threshold
from regression import regression_check
def test_m224():
 a={"technical_score":1,"semantic_score":1,"visual_score":1,"consistency_score":1}
 q=quality_score(a); assert classify(q["score"])=="EXCELLENT"
 assert above_threshold(perceptual_similarity({"features":["a"]},{"features":["a"]}))
 assert regression_check({"x":1},{"x":1})["passed"]
