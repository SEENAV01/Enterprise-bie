from .common import *
from .input_contracts import DiagnosticStep
def define(ctx):return make_definition(ctx,'mechanic:diagnose-error',MechanicKind.DIAGNOSE_ERROR,'Learner locates the first evidence-backed divergence in a worked process, not merely the final wrong answer.',(action('select:error-step',ActionKind.SELECT,'Select the first incorrect step','Arrow keys then Enter','diagnostic:steps'),),(motion('motion:diagnose',MotionSemantic.HIGHLIGHT,'diagnostic:steps','Focus attention on the first causal error and its correction.','error_step'),),('semantic_motion','keyboard_input','state_machine'))
def execute(ctx,state,steps):
 d=define(ctx)
 if not isinstance(steps,(tuple,list)) or not steps:raise MechanicError('GAME_MECH_DIAGNOSE_STEPS')
 typed=tuple(DiagnosticStep.from_mapping(s,i) for i,s in enumerate(steps));bad=[i for i,s in enumerate(typed) if s.actual!=s.expected]
 first=bad[0] if bad else None;after={**state,'first_error_index':first,'diagnosis_complete':True};out={'first_error_index':first,'error_indexes':tuple(bad),'evidence_ref':typed[first].evidence_ref if first is not None else None};return after,out,receipt(d,state,after,{'step_count':len(steps)},out)
