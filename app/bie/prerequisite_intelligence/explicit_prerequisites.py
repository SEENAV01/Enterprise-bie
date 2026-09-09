from __future__ import annotations
from dataclasses import dataclass
import re
@dataclass(frozen=True)
class ExplicitPrerequisite:
    prerequisite: str
    dependent: str
    evidence: str
    confidence: float = 1.0
_PATTERNS=(
 re.compile(r"(?:requires|prerequisite(?:s)?(?: are| is)?|depends on)\s+([^.;:]+)",re.I),
 re.compile(r"(?:recall|review|using)\s+([^.;:]+?)\s+(?:before|to understand|we can)",re.I),
)
def extract_explicit_prerequisites(dependent: str, text: str) -> list[ExplicitPrerequisite]:
    if not dependent.strip(): raise ValueError("dependent is required")
    out=[]; seen=set()
    for p in _PATTERNS:
        for m in p.finditer(text or ""):
            raw=re.sub(r"\s+"," ",m.group(1)).strip(" ,")
            for item in re.split(r"\s*(?:,| and )\s*",raw):
                key=item.casefold()
                if item and key not in seen:
                    seen.add(key); out.append(ExplicitPrerequisite(item,dependent,m.group(0).strip()))
    return out
