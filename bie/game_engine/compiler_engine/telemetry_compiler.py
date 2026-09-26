from __future__ import annotations
from .provenance_adapter import all_refs
import json,re
from .contracts import *
_FORBIDDEN=('source_text','answer_text','student_name','email','phone','prompt_text','book_text','raw_text')
def compile_telemetry(ctx:CompilerContext):
    ctx.validate();events=tuple(sorted(ctx.telemetry_allowlist))
    if not events:raise GameCompilerError('GAME_COMP_TELEMETRY_EMPTY')
    for e in events:
        if any(x in e.lower() for x in _FORBIDDEN):raise GameCompilerError('GAME_COMP_TELEMETRY_SENSITIVE',e)
    payload_allowlist=('event','game_id','level_id','challenge_id','attempt_number','outcome_code','mechanic_id','duration_bucket','objective_id','adaptation_id')
    data={'schema_version':'bie.game.telemetry-program/1','events':events,'payload_allowlist':payload_allowlist,'raw_text_allowed':False,'remote_endpoint':None,'consent_required':True,'local_sink_only':True,'sequence_ids_required':True,'product_accepted':False}
    ts='export const telemetryProgram = '+json.dumps(data,sort_keys=True,separators=(',',':'))+' as const;\nexport function sanitizeTelemetry(input: Record<string, unknown>): Record<string, unknown> { const out: Record<string, unknown> = {}; for (const key of telemetryProgram.payload_allowlist) { if (key in input) out[key] = input[key]; } return out; }\n'
    refs=all_refs(ctx.document.provenance);return artifact(ArtifactKind.TELEMETRY_PROGRAM,'runtime/telemetry.ts','text/typescript',ts,refs)
