from dataclasses import dataclass
@dataclass(frozen=True)
class Metric:
 name:str; score:float; floor:float
@dataclass(frozen=True)
class Benchmark:
 passed:bool; failures:tuple[str,...]; aggregate:float
def evaluate(metrics:list[Metric],required_domains:set[str],observed_domains:set[str])->Benchmark:
 if not metrics:raise ValueError("metrics required")
 for m in metrics:
  if not 0<=m.score<=1 or not 0<=m.floor<=1:raise ValueError("scores/floors must be normalized")
 f=[m.name for m in metrics if m.score<m.floor]
 missing=sorted(required_domains-observed_domains)
 f += ["missing_domain:"+d for d in missing]
 return Benchmark(not f,tuple(f),sum(m.score for m in metrics)/len(metrics))
