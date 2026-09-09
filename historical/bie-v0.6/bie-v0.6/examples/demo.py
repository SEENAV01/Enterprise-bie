
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from bie_m6.planner import Unit, build_lesson

units=[
 Unit("charge","Electric charge",importance=.9),
 Unit("field","Electric field",importance=1,prerequisite_ids=["charge"]),
 Unit("flux","Electric flux",importance=.8,prerequisite_ids=["field"]),
 Unit("wireless","Wireless power transfer",kind="application",importance=.6,
      prerequisite_ids=["field"])
]
print(json.dumps(build_lesson(units,"Electric Field Foundations",15),indent=2))
