BLOCKS=[
"HOOK","OBJECTIVE","PREREQUISITE_RECALL","CONTEXT",
"INTUITION","CORE_EXPLANATION","MECHANISM","DERIVATION",
"WORKED_EXAMPLE","APPLICATION","COMPARISON","MISCONCEPTION_CHECK",
"GUIDED_PRACTICE","RECAP","ASSESSMENT","ENRICHMENT"
]

def block(block_id, block_type, purpose, knowledge_ids=None, mode=None):
    return {"id":block_id,"type":block_type,"purpose":purpose,
            "knowledge_ids":knowledge_ids or [],"mode":mode}
