from dataclasses import dataclass
@dataclass(frozen=True)
class BookCase:
 domain:str; expected:set[tuple[str,str]]; predicted:set[tuple[str,str]]
@dataclass(frozen=True)
class BenchmarkReport:
 precision:float; recall:float; f1:float; domains:tuple[str,...]; cases:int
def evaluate(cases:list[BookCase])->BenchmarkReport:
 tp=fp=fn=0
 for c in cases:
  tp+=len(c.expected&c.predicted);fp+=len(c.predicted-c.expected);fn+=len(c.expected-c.predicted)
 precision=tp/(tp+fp) if tp+fp else 1.0
 recall=tp/(tp+fn) if tp+fn else 1.0
 f1=2*precision*recall/(precision+recall) if precision+recall else 0
 return BenchmarkReport(round(precision,6),round(recall,6),round(f1,6),tuple(sorted({c.domain for c in cases})),len(cases))
def acceptance_ready(report:BenchmarkReport,min_f1:float=.9,min_domains:int=5)->bool:
 return report.f1>=min_f1 and len(report.domains)>=min_domains and report.cases>=min_domains
