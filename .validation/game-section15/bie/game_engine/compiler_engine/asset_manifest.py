from __future__ import annotations
import json
from .provenance_adapter import all_refs
from .contracts import *
def compile_asset_manifest(ctx:CompilerContext):
    ctx.validate();required=set()
    for exp in ctx.document.experiences:
      for level in exp.levels:
        for cue in level.audio.cues:
          if cue.asset_ref:required.add(cue.asset_ref)
    missing=sorted(x for x in required if x not in ctx.assets)
    if missing:raise GameCompilerError('GAME_COMP_ASSET_MISSING',','.join(missing))
    rows=[]
    for ref in sorted(required):
        a=ctx.assets[ref].validate();row={'asset_ref':a.asset_ref,'media_type':a.media_type,'content_sha256':a.content_sha256,'alt_text':a.alt_text}
        if ctx.experience_profile is not None:
            rr=ctx.experience_profile.rights_map()[ref];row.update({'rights_ref':rr.rights_ref,'license_id':rr.license_id,'attribution':rr.attribution,'source_ref':rr.source_ref})
        rows.append(row)
    data={'schema_version':'bie.game.asset-manifest/1','assets':rows,'all_required_resolved':True,'product_accepted':False}
    return artifact(ArtifactKind.ASSET_MANIFEST,'runtime/assets.json','application/json',json.dumps(data,sort_keys=True,separators=(',',':')),all_refs(ctx.document.provenance))
