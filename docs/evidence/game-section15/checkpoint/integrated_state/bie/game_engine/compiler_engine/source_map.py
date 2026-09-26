from __future__ import annotations
from .provenance_adapter import all_refs
from dataclasses import dataclass
from ..canonical import canonical_json,fingerprint
from .contracts import CompilerContext,ArtifactKind,artifact
from .provenance_adapter import refs_by_role
@dataclass(frozen=True)
class SourceBinding:
    runtime_ref:str;source_refs:tuple[str,...];reasoning_refs:tuple[str,...];objective_refs:tuple[str,...]

def build_source_map(ctx:CompilerContext):
    refs=ctx.document.provenance.refs
    sources=refs_by_role(ctx.document.provenance,'source');reason=refs_by_role(ctx.document.provenance,'reasoning');objectives=refs_by_role(ctx.document.provenance,'objective')
    rows=[]
    for exp in ctx.document.experiences:
        for level in exp.levels:
            rows.append({'runtime_ref':level.level_id,'source_refs':sources,'reasoning_refs':reason,'objective_refs':objectives})
            for ch in level.challenges:rows.append({'runtime_ref':ch.challenge_id,'source_refs':sources,'reasoning_refs':reason,'objective_refs':objectives})
    body={'schema_version':'bie.game.source-map/1','bindings':rows,'product_accepted':False}
    return artifact(ArtifactKind.SOURCE_MAP,'runtime/source-map.json','application/json',canonical_json(body).decode(),sources+reason+objectives)
