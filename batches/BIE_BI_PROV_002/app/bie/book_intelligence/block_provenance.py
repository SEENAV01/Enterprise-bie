class E(ValueError):pass
METHODS={"native","ocr","hybrid","structured"}
def validate(block_id,anchor_ids,method):
 if not block_id or not anchor_ids or len(set(anchor_ids))!=len(anchor_ids) or method not in METHODS:raise E("provenance")
 return True
