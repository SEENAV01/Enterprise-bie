def entity(entity_id, entity_type, dataset_id=None,
           attributes=None):
    return {"entity_id":entity_id,"entity_type":entity_type,
            "dataset_id":dataset_id,"attributes":attributes or {}}

def belongs_to(record,dataset_id):
    return record["dataset_id"]==dataset_id
