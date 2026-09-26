from .common import *
def define(ctx):return make_definition(ctx,'mechanic:misconception-trap',MechanicKind.MISCONCEPTION_TRAP,'Learner encounters a plausible misconception-linked choice and receives targeted evidence-grounded correction.',(action('select:choice',ActionKind.SELECT,'Choose an explanation','Arrow keys then Enter','misconception:choices'),),(motion('motion:highlight',MotionSemantic.HIGHLIGHT,'misconception:choices','Highlight the conceptual conflict without relying on color alone.','diagnostic_state'),),('semantic_motion','keyboard_input','state_machine'))
def execute(ctx,state,choice,options):
 d=define(ctx)
 if choice not in options:raise MechanicError('GAME_MECH_MISCONCEPTION_UNKNOWN_CHOICE')
 row=options[choice]
 if 'correct' not in row or 'feedback_ref' not in row:raise MechanicError('GAME_MECH_MISCONCEPTION_OPTION')
 if row.get('misconception_id') and not row.get('evidence_ref'):raise MechanicError('GAME_MECH_MISCONCEPTION_EVIDENCE')
 after={**state,'choice':choice,'correct':bool(row['correct']),'feedback_ref':row['feedback_ref']};out={'correct':bool(row['correct']),'misconception_id':row.get('misconception_id'),'feedback_ref':row['feedback_ref'],'evidence_ref':row.get('evidence_ref')};return after,out,receipt(d,state,after,{'choice':choice},out)
