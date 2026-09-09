
from dataclasses import dataclass
class EmbeddingError(ValueError):pass
@dataclass(frozen=True)
class EmbeddingResult:model:str;vectors:tuple;dimensions:int
def validate(result,input_count):
 if len(result.vectors)!=input_count:raise EmbeddingError("cardinality mismatch")
 if result.dimensions<1:raise EmbeddingError("dimensions")
 if any(len(v)!=result.dimensions for v in result.vectors):raise EmbeddingError("dimension mismatch")
 return True
