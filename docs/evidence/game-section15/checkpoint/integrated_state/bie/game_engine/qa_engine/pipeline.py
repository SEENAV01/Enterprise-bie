from __future__ import annotations
from ..canonical import fingerprint
from .qa_001 import evaluate as q1
from .qa_002 import evaluate as q2
from .qa_003 import evaluate as q3
from .qa_004 import evaluate as q4
from .qa_005 import evaluate as q5
from .qa_006 import evaluate as q6
from .qa_007 import evaluate as q7
from .qa_008 import evaluate as q8
from .qa_009 import evaluate as q9
from .qa_010 import evaluate as q10
from .contracts import GameQAReport
from .policy import GameQAPolicy
from .candidate import CandidateGameEvidence

def run_game_qa(candidate:CandidateGameEvidence,policy=GameQAPolicy()):
    policy.validate();candidate.validate();targets=dict(candidate.challenge_targets)
    results=(q1(candidate.signals.objectives,candidate.plans,candidate.signals.provenance,policy),q2(candidate.document,candidate.compiled_bundle),q3(candidate.transition_system,candidate.start_state_id,targets,candidate.evidence_refs),q4(candidate.transition_system,candidate.start_state_id,candidate.goal_state_ids,policy,candidate.evidence_refs),q5(candidate.signals,candidate.plans[0]),q6(candidate.document,candidate.compiled_bundle),q7(candidate.document,candidate.compiled_bundle,candidate.runtime_result.browser,policy),q8(candidate.runtime_result,policy),q9(candidate.benchmark_records,policy),q10(candidate.source_root))
    fp=fingerprint({'candidate':candidate.fingerprint(),'results':tuple(r.result_fingerprint for r in results)});return GameQAReport(results,fp,all(r.status.value=='pass' for r in results),True,False).validate()
