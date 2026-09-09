
def repair_actions(report):
    a=[]
    if report["faithfulness"]<.90:a.append("Re-verify unsupported or weak claims against source passages.")
    if report["coverage"]<.90:a.append("Run missing-information retrieval and extraction.")
    if report["relation_accuracy"]<.90:a.append("Re-check graph relations using paired evidence.")
    if report["provenance"]<1.0:a.append("Attach source provenance to every claim.")
    if report["external_evidence"]<1.0:a.append("Verify every external node with authoritative evidence.")
    if not report["cycle_free"]:a.append("Repair prerequisite cycles before learning-order generation.")
    return a
