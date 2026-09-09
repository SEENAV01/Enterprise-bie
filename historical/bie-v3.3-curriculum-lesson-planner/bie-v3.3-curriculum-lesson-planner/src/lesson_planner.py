from objectives import normalize_objective
from sequence import prioritize
from lesson_blocks import block

def plan_lesson(objective, nodes, dependencies, evidence_by_node, applications=None):
    obj=normalize_objective(objective)
    seq=prioritize(nodes,dependencies,obj["topic"])
    if seq["status"]!="READY":
        return {"schema_version":"3.3","status":seq["status"],"objective":obj,"blocks":[]}

    blocks=[]
    target_seq=seq["sequence"]

    # Teaching sequence is evidence/dependency driven, not duration driven.
    for node_id in target_seq:
        ev=evidence_by_node.get(node_id,[])
        if node_id != obj["topic"]:
            blocks.append(block("PREREQUISITE_REVIEW",node_id,ev,"simple_recall_or_visual_recap"))
        else:
            blocks.append(block("ORIENTATION",node_id,ev,"context_visual"))
            blocks.append(block("DEFINITION",node_id,ev,"definition_card"))
            blocks.append(block("INTUITION",node_id,ev,"conceptual_visual"))
            blocks.append(block("MECHANISM",node_id,ev,"process_or_system_animation"))
            if obj["type"] in ["DERIVE","SOLVE"]:
                blocks.append(block("DERIVATION",node_id,ev,"stepwise_equation_animation"))
            blocks.append(block("WORKED_EXAMPLE",node_id,ev,"worked_example"))
            blocks.append(block("APPLICATION",node_id,ev,"real_world_application"))
            blocks.append(block("CHECKPOINT",node_id,ev,"question_visual"))
            blocks.append(block("TRANSFER",node_id,ev,"new_situation"))

    return {
      "schema_version":"3.3",
      "status":"READY",
      "objective":obj,
      "sequence":target_seq,
      "blocks":blocks,
      "timing_policy":"CONTENT_AND_AUDIO_DRIVEN"
    }
