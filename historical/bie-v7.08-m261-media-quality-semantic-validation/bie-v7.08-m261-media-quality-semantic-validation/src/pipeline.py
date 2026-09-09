from visual import validate_visual,semantic_match
from diagram import validate_diagram
from audio import validate_audio
from captions import validate_caption_sync
from accessibility import validate_accessibility
from engine import aggregate,repair_candidates

def build_m261_runtime():
    visual={"output_uri":"media/field.png","metadata":{"resolution":"1920x1080","concepts":["electric-field"]}}
    diagram={"nodes":[{"id":"q","label":"Charge"},{"id":"e","label":"Field"}],
             "edges":[{"source":"q","target":"e"}]}
    audio={"uri":"media/narration.wav","duration_seconds":3.2,"lufs":-18,"clipping":False}
    captions=[{"start":0,"end":2.3,"text":"Electric field is a vector field."}]
    scene={"text_contrast_ratio":7.1,"narration_present":True,"captions_present":True}
    results={"visual":validate_visual(visual,{"metadata":{"resolution":"1920x1080"}}),
             "semantic":semantic_match(visual,["electric-field"]),
             "diagram":validate_diagram(diagram),
             "audio":validate_audio(audio,3.2),
             "captions":validate_caption_sync(captions,3.2),
             "accessibility":validate_accessibility(scene)}
    score=aggregate(results)
    candidates=repair_candidates(results)
    return {"schema_version":"7.08","results":results,"quality_summary":score,
            "repair_candidates":candidates,
            "media_quality_gate":{"valid":score["valid"],"score":score["score"],
                                  "errors":score["errors"]}}
