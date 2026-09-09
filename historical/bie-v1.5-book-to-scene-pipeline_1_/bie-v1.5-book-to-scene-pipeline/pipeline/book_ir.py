from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any
import re

@dataclass
class Passage:
    passage_id: str
    text: str
    page: int | None = None
    heading_path: List[str] = field(default_factory=list)

@dataclass
class Question:
    qid: str
    kind: str
    question: str
    evidence: List[str] = field(default_factory=list)
    answer: str | None = None

@dataclass
class ConceptUnit:
    unit_id: str
    title: str
    passages: List[str]
    questions: List[Question]
    definitions: List[str] = field(default_factory=list)
    processes: List[str] = field(default_factory=list)
    causes: List[str] = field(default_factory=list)
    time_place: List[str] = field(default_factory=list)
    people_entities: List[str] = field(default_factory=list)
    applications: List[str] = field(default_factory=list)
    higher_knowledge: List[Dict[str,Any]] = field(default_factory=list)
    uncertainty: List[str] = field(default_factory=list)

def classify_questions(text:str):
    patterns={
      "what":r"\b(what|define|definition|meaning)\b",
      "why":r"\b(why|because|reason|cause)\b",
      "how":r"\b(how|process|method|steps)\b",
      "when":r"\b(when|date|time|period)\b",
      "where":r"\b(where|location|place)\b",
      "who":r"\b(who|person|scientist|author)\b",
      "application":r"\b(use|application|applied|example|daily life)\b",
      "derivation":r"\b(derive|derivation|prove|proof)\b"
    }
    out=[]
    for kind,p in patterns.items():
        if re.search(p,text,re.I):
            out.append(kind)
    return out

def build_book_ir(passages:list[Passage])->dict:
    units=[]
    for i,p in enumerate(passages,1):
        kinds=classify_questions(p.text)
        qs=[asdict(Question(f"Q{i}-{k}",k,f"{k.upper()}: {p.text[:180]}",[p.passage_id])) for k in kinds]
        units.append(asdict(ConceptUnit(
            unit_id=f"U{i:04d}", title=p.heading_path[-1] if p.heading_path else f"Passage {i}",
            passages=[p.passage_id], questions=[Question(**q) for q in qs]
        )))
    return {"schema_version":"1.5","passages":[asdict(p) for p in passages],"units":units}
