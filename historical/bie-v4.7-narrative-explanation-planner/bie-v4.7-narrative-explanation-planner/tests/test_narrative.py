import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from narrative_engine import build_narrative
def test_narrative():
 r=build_narrative({
  "blocks":[{"id":"b","type":"DERIVATION","purpose":"derive","knowledge_ids":["x"],"mode":"DERIVE_STEP_BY_STEP"}],
  "adapted_units":[{"knowledge_id":"x","teaching_mode":"DERIVE_STEP_BY_STEP"}]})
 assert r["schema_version"]=="4.7"
 assert r["timing_policy"]["audio_drives_final_timing"]
 assert r["narrative_beats"][0]["beats"][0]=="START"
