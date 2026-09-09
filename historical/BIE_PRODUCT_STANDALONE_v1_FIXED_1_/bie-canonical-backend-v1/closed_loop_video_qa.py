from pathlib import Path
import json

def run_closed_loop(stages, max_repair_cycles=1):
    """
    Orchestrate the complete QA loop using injected stage callables.
    Every stage must return explicit status; no implicit success.
    """
    history=[]
    current=stages["initial"]

    for cycle in range(max_repair_cycles + 1):
        history.append({"cycle":cycle,"state":current})
        decision=current.get("decision")

        if decision=="accept":
            return {"status":"accepted","cycles":cycle,"history":history}
        if decision=="reject" and cycle < max_repair_cycles:
            repair=stages["repair"](current)
            if repair.get("status")!="success":
                return {"status":"repair_failed","cycles":cycle,"history":history,
                        "repair":repair}
            current=stages["rerender"](repair)
            if current.get("status")!="success":
                return {"status":"rerender_failed","cycles":cycle,"history":history,
                        "render":current}
            current=stages["qa"](current)
            continue
        return {"status":"review_required","cycles":cycle,"history":history}

    return {"status":"review_required","cycles":max_repair_cycles,"history":history}

def summarize_loop(result):
    return {
        "status":result.get("status"),
        "cycles":result.get("cycles",0),
        "accepted":result.get("status")=="accepted",
        "history_length":len(result.get("history",[]))
    }
