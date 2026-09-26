from .common import *
from .input_contracts import SimulationModel
def define(ctx):return make_definition(ctx,'mechanic:simulation',MechanicKind.SIMULATION_EXPERIMENT,'Learner varies declared model parameters and observes model-bounded consequences, never implied real-world truth.',(action('adjust:parameter',ActionKind.ADJUST,'Adjust simulation parameter','Arrow keys','simulation:parameter'),action('submit:run',ActionKind.SUBMIT,'Run the experiment','Enter','simulation:run')),(motion('motion:plot',MotionSemantic.PLOT,'simulation:plot','Plot the model response produced by learner-controlled parameters.','simulation_output'),),('semantic_motion','keyboard_input','state_machine','simulation'))
def execute(ctx,state,inputs,model):
 d=define(ctx)
 m=SimulationModel.from_mapping(model);xs=tuple(float(x) for x in inputs)
 if not xs:raise MechanicError('GAME_MECH_SIMULATION_INPUTS')
 a=m.coefficient;b=m.offset;ys=tuple(a*x+b for x in xs)
 after={**state,'last_inputs':xs,'last_outputs':ys};out={'model_scope':'DECLARED_LINEAR_MODEL','points':tuple(zip(xs,ys)),'parameter_fingerprint':fingerprint(model)};return after,out,receipt(d,state,after,{'inputs':xs,'model':model},out)
