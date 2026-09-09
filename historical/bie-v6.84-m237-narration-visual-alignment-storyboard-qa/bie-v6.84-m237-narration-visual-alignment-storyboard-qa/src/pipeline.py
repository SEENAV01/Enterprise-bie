from narration_quality import validate_narration
from visual_alignment import alignment,validate_alignment
from onscreen_text import plan_overlays,validate_overlays
from pedagogical_qa import storyboard_qa,pedagogical_gate

def build_pedagogical_qa_runtime():
    segments=[
      {"segment_id":"SEG-1","concept_ids":["c1"],"text":"Electric charge is a physical property."},
      {"segment_id":"SEG-2","concept_ids":["c2"],"text":"Electric field describes force per unit charge."}]
    shots=[
      {"shot_id":"SHOT-1","concept_ids":["c1"]},
      {"shot_id":"SHOT-2","concept_ids":["c2"]}]
    narration=validate_narration("Electric charge is a physical property.")
    records=[alignment(s,sh) for s,sh in zip(segments,shots)]
    align=validate_alignment(records)
    overlays=plan_overlays(segments)
    overlay_check=validate_overlays(overlays,max_words=18)
    sb=storyboard_qa(segments,shots,overlays,records)
    gate=pedagogical_gate(narration,align,overlay_check,sb)
    return {"schema_version":"6.84","segments":segments,"shots":shots,
            "narration_quality":narration,"visual_alignment":records,
            "alignment_validation":align,"overlays":overlays,
            "overlay_validation":overlay_check,"storyboard_qa":sb,
            "pedagogical_gate":gate}
