import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from evaluation import evaluate_outcome
from adaptation import adaptation_signal

def test_effective():
 o={"outcome_id":"1","delta":{"mastery_gain":.1}}
 assert evaluate_outcome(o)["effective"]

def test_negative_signal():
 o={"delta":{"mastery_gain":-.1},"post_state":{"uncertainty":.5}}
 assert adaptation_signal(o)["signal"]=="NEGATIVE"
