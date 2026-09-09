def transition(previous_block,current_block):
    return {
      "from":previous_block["id"] if previous_block else None,
      "to":current_block["id"],
      "type":"CONCEPTUAL_BRIDGE",
      "instruction":"Connect the previous mental model to the next idea; do not add unsupported facts."
    }

def build_transitions(blocks):
    return [transition(blocks[i-1] if i else None,b)
            for i,b in enumerate(blocks)]
