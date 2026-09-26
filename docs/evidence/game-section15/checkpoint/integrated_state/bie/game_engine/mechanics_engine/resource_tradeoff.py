from .common import *
def define(ctx):return make_definition(ctx,'mechanic:resource-tradeoff',MechanicKind.RESOURCE_TRADEOFF,'Learner allocates bounded resources and sees transparent opportunity costs rather than arbitrary score loss.',(action('adjust:resource',ActionKind.ADJUST,'Adjust resource allocation','Arrow keys','resource:allocation'),),(motion('motion:flow',MotionSemantic.FLOW,'resource:allocation','Visualize resource transfer and opportunity cost.','resource_state'),),('semantic_motion','keyboard_input','state_machine'))
def execute(ctx,state,delta,bounds):
 d=define(ctx);resources=dict(state.get('resources',{}))
 if not resources or set(delta)-set(resources) or set(bounds)!=set(resources):raise MechanicError('GAME_MECH_RESOURCE_SCHEMA')
 after_res=dict(resources)
 for k,dv in delta.items():
  if type(dv) not in (int,float):raise MechanicError('GAME_MECH_RESOURCE_DELTA')
  after_res[k]+=dv;lo,hi=bounds[k]
  if not lo<=after_res[k]<=hi:raise MechanicError('GAME_MECH_RESOURCE_BOUNDS',k)
 if all(v==0 for v in delta.values()):raise MechanicError('GAME_MECH_RESOURCE_NOOP')
 after={**state,'resources':after_res};out={'before':resources,'after':after_res,'delta':dict(delta),'opportunity_costs':tuple(sorted(k for k,v in delta.items() if v<0))};return after,out,receipt(d,state,after,{'delta':delta},out)
