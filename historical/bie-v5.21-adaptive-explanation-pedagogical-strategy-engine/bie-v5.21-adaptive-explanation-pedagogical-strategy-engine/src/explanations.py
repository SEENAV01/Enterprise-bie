def explanation_plan(concept_id,depth,components=None,
                     analogy=None,example_count=1):
    return {"concept_id":concept_id,"depth":depth,
            "components":components or ["INTUITION","FORMAL","EXAMPLE"],
            "analogy":analogy,"example_count":example_count}
