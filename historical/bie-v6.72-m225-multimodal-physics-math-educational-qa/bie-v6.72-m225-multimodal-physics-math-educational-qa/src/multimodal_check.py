def check_alignment(narration,visual,captions):
    n=set(narration.lower().split()); v=set(visual.lower().split()); c=set(captions.lower().split())
    overlap=n&v
    return {"semantic_overlap":len(overlap),"caption_overlap":len(overlap&c),"passed":len(overlap)>0}
def check_modalities(modalities):
    required={"narration","visual","captions"}; missing=sorted(required-set(modalities))
    return {"missing":missing,"passed":not missing}
