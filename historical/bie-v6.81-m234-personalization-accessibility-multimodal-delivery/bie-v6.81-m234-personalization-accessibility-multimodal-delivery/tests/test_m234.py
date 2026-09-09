import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from preferences import learner_preferences,validate_preferences
from accessibility import accessibility_profile
from policies import personalization_policy
from delivery import select_delivery
def test_m234():
 p=learner_preferences("x","hi"); assert validate_preferences(p)
 a=accessibility_profile(captions=True)
 policy=personalization_policy(p,a)
 assert policy["captions"]
 assert select_delivery(policy,["CAPTIONED_VIDEO"])["selected"]==["CAPTIONED_VIDEO"]
