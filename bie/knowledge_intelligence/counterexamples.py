class E(ValueError):pass
def create(example_id,concept_id,violated_rule,anchor_id,confidence):
 if not all((example_id,concept_id,violated_rule.strip(),anchor_id)) or not 0<=confidence<=1:raise E("counterexample")
 return {"example_id":example_id,"concept_id":concept_id,"type":"COUNTEREXAMPLE","violated_rule":violated_rule.strip(),"anchor_id":anchor_id,"confidence":confidence}
