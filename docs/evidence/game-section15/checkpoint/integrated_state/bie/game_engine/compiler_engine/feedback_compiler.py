from __future__ import annotations
from .provenance_adapter import all_refs
import json
from .contracts import *
def _text(ctx,ref):
    if ref not in ctx.text_catalog:raise GameCompilerError('GAME_COMP_TEXT_REF_MISSING',ref)
    return ctx.text_catalog[ref]
def compile_feedback(ctx:CompilerContext):
    ctx.validate();rows=[]
    for exp in ctx.document.experiences:
      for level in exp.levels:
       for ch in level.challenges:
        f=ch.feedback.validate();rows.append({'challenge_id':ch.challenge_id,'success':_text(ctx,f.success_message_ref),'failure':_text(ctx,f.failure_message_ref),'misconceptions':[{'misconception_id':m,'message':_text(ctx,r)} for m,r in f.misconception_feedback],'explanation':_text(ctx,f.explanation_ref) if f.explanation_ref else None,'reveal_answer_on_failure':False})
    data={'schema_version':'bie.game.feedback-program/1','feedback':rows,'product_accepted':False};ts='export const feedbackProgram = '+json.dumps(data,sort_keys=True,separators=(',',':'))+' as const;\n'
    refs=all_refs(ctx.document.provenance);return artifact(ArtifactKind.FEEDBACK_PROGRAM,'runtime/feedback.ts','text/typescript',ts,refs)
