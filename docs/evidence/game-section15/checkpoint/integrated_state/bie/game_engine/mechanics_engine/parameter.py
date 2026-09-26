from .common import *
def define(ctx):return make_definition(ctx,'mechanic:parameter',MechanicKind.MANIPULATE_PARAMETER,'Learner changes a bounded parameter and observes a causally bound visual/state response.',(action('adjust:value',ActionKind.ADJUST,'Adjust the parameter','Arrow keys','parameter:value'),),(motion('motion:value',MotionSemantic.VALUE_CHANGE,'parameter:value','Show the parameter change and its causal effect.','parameter:value'),),('semantic_motion','keyboard_input','state_machine'))
def execute(ctx,state,delta=1.0,bounds=(0.0,10.0)):
 d=define(ctx);x=bounded_number(state.get('value'),bounds[0],bounds[1],'GAME_MECH_PARAMETER_STATE');delta=bounded_number(delta,-1000,1000,'GAME_MECH_PARAMETER_DELTA');nv=x+delta
 if not bounds[0]<=nv<=bounds[1]:raise MechanicError('GAME_MECH_PARAMETER_RANGE')
 after={**state,'value':nv};out={'delta':delta,'bounded':True,'visual_semantic':'value_change'};return after,out,receipt(d,state,after,{'delta':delta},out)
