SUPPORTED_BLOCKS = {
    "HOOK","OBJECTIVE","EXPLANATION","EXAMPLE","DEMONSTRATION",
    "CHECK_FOR_UNDERSTANDING","MISCONCEPTION_REPAIR","SUMMARY",
    "RETRIEVAL_PROMPT","TRANSITION"
}

def block(block_id, block_type, text, objective_ids=None,
          evidence_ids=None, order=0, duration_sec=None):
    if block_type not in SUPPORTED_BLOCKS:
        raise ValueError("UNSUPPORTED_SCRIPT_BLOCK")
    return {"block_id":block_id,"block_type":block_type,"text":text,
            "objective_ids":objective_ids or [],
            "evidence_ids":evidence_ids or [],
            "order":order,"duration_sec":duration_sec}

def valid(item):
    return bool(item["block_id"] and item["text"]) and item["block_type"] in SUPPORTED_BLOCKS

def ordered(blocks):
    return sorted(blocks,key=lambda x:x["order"])
