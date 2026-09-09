def narration_instruction(block,unit=None):
    purpose=block.get("purpose","")
    mode=block.get("mode","EXPLAIN")
    return {
      "block_id":block["id"],
      "mode":mode,
      "purpose":purpose,
      "instruction":(
        "Write a learner-facing explanation that is accurate, coherent, "
        "source-grounded, and explicit about reasoning. Avoid filler. "
        "Introduce symbols before using them, explain causal links, and "
        "connect each step to the learner's mental model."
      )
    }

def build_script_plan(blocks,units_by_id):
    return [narration_instruction(
        b,units_by_id.get(b.get("knowledge_ids",[None])[0],{})
      ) for b in blocks]
