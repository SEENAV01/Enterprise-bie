from .common import *
def define(ctx):return make_definition(ctx,'mechanic:prediction',MechanicKind.PREDICTION_OBSERVE,'Learner commits a prediction before observation, then compares prediction with evidence.',(action('predict:value',ActionKind.PREDICT,'Commit prediction','Type value then Enter','prediction:value'),action('submit:observe',ActionKind.SUBMIT,'Reveal observation','Enter','prediction:observe')),(motion('motion:compare',MotionSemantic.COMPARE,'prediction:compare','Contrast committed prediction with observed result after commitment.','prediction_error'),),('semantic_motion','keyboard_input','state_machine'))
def execute(ctx,state,prediction,observation,committed):
 d=define(ctx)
 if committed is not True:raise MechanicError('GAME_MECH_PREDICTION_COMMIT_REQUIRED')
 if state.get('observation_revealed'):raise MechanicError('GAME_MECH_PREDICTION_OBSERVATION_ALREADY_REVEALED')
 err=abs(float(prediction)-float(observation)) if type(prediction) in (int,float) and type(observation) in (int,float) else (0 if prediction==observation else None)
 after={**state,'prediction':prediction,'observation':observation,'observation_revealed':True,'error':err};out={'match':prediction==observation,'absolute_error':err,'prediction_committed_before_observation':True};return after,out,receipt(d,state,after,{'prediction':prediction},out)
