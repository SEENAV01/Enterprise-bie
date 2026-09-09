BLOCK_TYPES=[
"ORIENTATION","PREREQUISITE_REVIEW","DEFINITION","INTUITION",
"MECHANISM","DERIVATION","WORKED_EXAMPLE","APPLICATION",
"COMPARISON","MISCONCEPTION","CHECKPOINT","RECAP","TRANSFER"
]

def block(block_type, objective, evidence_ids=None, visual_intent=None):
    return {
      "type":block_type,
      "objective":objective,
      "evidence_ids":evidence_ids or [],
      "visual_intent":visual_intent,
      "status":"PLANNED"
    }
