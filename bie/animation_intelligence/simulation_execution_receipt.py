from dataclasses import dataclass

class SimulationReceiptError(ValueError): pass

@dataclass(frozen=True)
class SimulationExecutionReceipt:
    receipt_id:str
    engine:str
    engine_version:str
    model_fingerprint:str
    seed:int
    input_hash:str
    output_hash:str
    observed_execution:bool
    verified:bool
    deterministic:bool
    review_required:bool=True
    accepted:bool=False

def _hash(v):
    return isinstance(v,str) and len(v)==64 and all(c in "0123456789abcdef" for c in v.lower())

def validate_receipt(r):
    if not r.receipt_id or not r.engine or not r.engine_version:
        raise SimulationReceiptError("identity missing")
    if not _hash(r.model_fingerprint) or not _hash(r.input_hash) or not _hash(r.output_hash):
        raise SimulationReceiptError("invalid execution hash")
    if isinstance(r.seed,bool) or not isinstance(r.seed,int):
        raise SimulationReceiptError("invalid seed")
    if r.observed_execution and not r.verified:
        raise SimulationReceiptError("observed execution must be verified")
    return True

def classify_simulation_claim(receipt=None,declared_model_output=False):
    if receipt is None:
        return "DECLARED_MODEL_OUTPUT" if declared_model_output else "CONCEPTUAL_ANIMATION"
    validate_receipt(receipt)
    if receipt.observed_execution and receipt.verified:
        return "VERIFIED_OBSERVED_EXECUTION"
    return "DECLARED_MODEL_OUTPUT"
