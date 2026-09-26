from __future__ import annotations
from .provenance_adapter import all_refs
import json
from .contracts import *
def compile_scoring(ctx:CompilerContext):
    ctx.validate();resolved={}
    for exp in ctx.document.experiences:
        if exp.scoring_policy_ref not in ctx.scoring_policies:raise GameCompilerError('GAME_COMP_SCORING_POLICY_MISSING',exp.scoring_policy_ref)
        p=ctx.scoring_policies[exp.scoring_policy_ref].validate();resolved[exp.game_id]={'policy_id':p.policy_id,'correct_points':p.correct_points,'incorrect_points':p.incorrect_points,'hint_cost':p.hint_cost,'floor':p.floor,'mastery_weighted':p.mastery_weighted,'speed_pressure':False}
    data={'schema_version':'bie.game.scoring-program/1','games':resolved,'product_accepted':False};ts='export const scoringProgram = '+json.dumps(data,sort_keys=True,separators=(',',':'))+' as const;\n'
    refs=all_refs(ctx.document.provenance);return artifact(ArtifactKind.SCORING_PROGRAM,'runtime/scoring.ts','text/typescript',ts,refs)
