from dataclasses import dataclass,asdict
from typing import Optional

@dataclass
class Evidence:
    evidence_id:str
    source_id:str
    page:Optional[int]
    quote:str
    start_char:Optional[int]=None
    end_char:Optional[int]=None

def claim_record(claim_id,text,evidence:list[Evidence],kind="source_derived"):
    return {
      "claim_id":claim_id,
      "text":text,
      "kind":kind,
      "evidence":[asdict(x) for x in evidence],
      "status":"GROUNDED" if evidence else "UNSUPPORTED"
    }
