from pathlib import Path
from typing import Callable, Dict, Any

REQUIRED_ADAPTERS = (
    "render",
    "frame_sample",
    "ocr",
    "semantic_qa",
    "repair",
    "regenerate",
)

class ProductionLoopError(RuntimeError):
    pass

def validate_adapters(adapters: Dict[str, Callable[..., Any]]):
    missing=[name for name in REQUIRED_ADAPTERS
             if not callable(adapters.get(name))]
    if missing:
        raise ProductionLoopError(
            "MISSING_PRODUCTION_ADAPTERS:" + ",".join(missing)
        )
    return True

def run_production_cycle(adapters, payload, max_cycles=1):
    """
    Production wiring layer around M297.
    Every adapter is injected, making the loop executable without hidden
    implementation assumptions.
    """
    validate_adapters(adapters)
    history=[]
    current=dict(payload)

    for cycle in range(max_cycles+1):
        render=adapters["render"](current)
        if render.get("status")!="success":
            return {"status":"render_failed","cycle":cycle,
                    "history":history+[{"cycle":cycle,"render":render}]}
        sample=adapters["frame_sample"](render)
        ocr=adapters["ocr"](sample)
        qa=adapters["semantic_qa"](current,ocr)

        record={"cycle":cycle,"render":render,"sample":sample,"ocr":ocr,"qa":qa}
        history.append(record)

        decision=qa.get("decision")
        if decision=="accept":
            return {"status":"accepted","cycle":cycle,"history":history}
        if decision!="reject" or cycle>=max_cycles:
            return {"status":"review_required","cycle":cycle,"history":history}

        repaired=adapters["repair"](current,qa)
        if repaired.get("status")!="success":
            return {"status":"repair_failed","cycle":cycle,
                    "history":history,"repair":repaired}
        regenerated=adapters["regenerate"](repaired)
        if regenerated.get("status")!="success":
            return {"status":"regeneration_failed","cycle":cycle,
                    "history":history,"regeneration":regenerated}
        current=regenerated.get("payload",current)

    return {"status":"review_required","history":history}
