from .common import *
def define(ctx):return make_definition(ctx,'mechanic:spatial-arrangement',MechanicKind.SPATIAL_ARRANGEMENT,'Learner arranges semantic objects in space so relative position itself carries conceptual meaning.',(action('place:entity',ActionKind.PLACE,'Place the selected object','Arrow keys then Enter','layout:board'),),(motion('motion:arrange',MotionSemantic.REORDER,'layout:board','Reveal spatial relationships caused by learner placement.','layout'),),('semantic_motion','keyboard_input','state_machine'))
def execute(ctx,state,placements,constraints):
 d=define(ctx)
 if not isinstance(placements,dict) or len(placements)<2:raise MechanicError('GAME_MECH_SPATIAL_PLACEMENTS')
 if any(not isinstance(v,(tuple,list)) or len(v)!=2 for v in placements.values()):raise MechanicError('GAME_MECH_SPATIAL_COORDINATE')
 violations=[]
 for left,right,relation in constraints:
  if left not in placements or right not in placements:raise MechanicError('GAME_MECH_SPATIAL_UNKNOWN_ENTITY')
  if relation=='left_of' and not placements[left][0]<placements[right][0]:violations.append((left,right,relation))
  elif relation=='above' and not placements[left][1]>placements[right][1]:violations.append((left,right,relation))
  elif relation not in {'left_of','above'}:raise MechanicError('GAME_MECH_SPATIAL_RELATION')
 after={**state,'placements':tuple(sorted((k,tuple(v)) for k,v in placements.items())),'valid':not violations};out={'violations':tuple(violations),'constraint_count':len(constraints)};return after,out,receipt(d,state,after,{'placements':placements},out)
