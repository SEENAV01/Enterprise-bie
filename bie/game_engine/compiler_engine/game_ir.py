from __future__ import annotations
from .provenance_adapter import all_refs
from ..codec import encode
from ..canonical import canonical_json
from .contracts import *
def compile_game_ir(ctx:CompilerContext):
    ctx.validate();wire=encode(ctx.document);body={'schema_version':'bie.game.compiled-ir/1','document':wire,'document_fingerprint':ctx.document.fingerprint(),'compile_profile':ctx.compile_profile,'product_accepted':False}
    refs=all_refs(ctx.document.provenance)
    return artifact(ArtifactKind.GAME_IR,'runtime/game-ir.json','application/json',canonical_json(body).decode(),refs)
