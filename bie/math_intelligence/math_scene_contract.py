from dataclasses import dataclass
@dataclass(frozen=True)
class MathSceneCue:
 cue_type:str; before:str; after:str|None; targets:tuple[str,...]; semantic_reason:str
ALLOWED={"equation_reveal","equation_morph","substitute","cancel","highlight_term","graph_transform","geometry_construct"}
def cue(kind,before,after=None,targets=(),reason=""):
 if kind not in ALLOWED:raise ValueError("unsupported math scene cue")
 if not before.strip() or not reason.strip():raise ValueError("semantic evidence required")
 if kind in {"equation_morph","substitute","graph_transform"} and not (after or "").strip():raise ValueError("after state required")
 return MathSceneCue(kind,before,after,tuple(targets),reason)
