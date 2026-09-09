class E(ValueError):pass
LEVELS={"book","chapter","section","subsection","local"}
def assign(concept_id,level,container_ids):
 if not concept_id or level not in LEVELS or not container_ids:raise E("scope")
 return {"concept_id":concept_id,"level":level,"containers":tuple(dict.fromkeys(container_ids))}
