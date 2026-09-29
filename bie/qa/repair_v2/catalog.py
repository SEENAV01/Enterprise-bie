"""Small exact default routing catalog; unknown codes always need triage.

This is an extensible operator policy seed, not a completeness claim. Report owner
strings or keyword matches never change the destination. No route dispatch occurs.
"""
from .models import FailureRule

def baseline_rules():
    rows=[
      ('BIE-QA-GAME-001','GAME_BUILD_EXECUTION_FAILED','CONTENT','GAME',True),
      ('BIE-QA-GAME-001','GAME_BUILD_STALE','EVIDENCE','QA',False),
      ('BIE-QA-GAME-001','GAME_BUILD_ARTIFACT_LINK','EVIDENCE','QA',False),
      ('BIE-QA-GAME-002','GAME_NON_NATIVE_RUNTIME','ENVIRONMENT','INFRA',False),
      ('BIE-QA-GAME-002','GAME_CONSOLE_ERROR','CONTENT','GAME',True),
      ('BIE-QA-AUDIO-001','AUDIO_PLACEMENT','CONTENT','AUDIO',True),
      ('BIE-QA-AUDIO-001','AUDIO_VOICE_OR_LANGUAGE','CONTENT','AUDIO',True),
      ('BIE-QA-AUDIO-001','AUDIO_REVIEW_MISSING','EVIDENCE','QA',False),
      ('BIE-QA-VIS-001','VIS_CONTEXT_REVIEW_MISSING','EVIDENCE','QA',False),
    ]
    return tuple(FailureRule(*r) for r in rows)
