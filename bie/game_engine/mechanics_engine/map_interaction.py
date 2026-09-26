from math import radians,sin,cos,sqrt,atan2
from .common import *
from .input_contracts import SourcedMapLocation
def define(ctx):return make_definition(ctx,'mechanic:map',MechanicKind.MAP_INTERACTION,'Learner explores sourced locations and spatial relationships without fabricated coordinates.',(action('select:location',ActionKind.SELECT,'Select location','Tab then Enter','map:location'),),(motion('motion:map',MotionSemantic.FOCUS,'map:location','Focus the learner on the selected spatial evidence.','selected_location'),),('semantic_motion','keyboard_input','state_machine','map'))
def _distance(a,b):
 lat1,lon1,lat2,lon2=map(radians,(a[0],a[1],b[0],b[1]));dlat=lat2-lat1;dlon=lon2-lon1;x=sin(dlat/2)**2+cos(lat1)*cos(lat2)*sin(dlon/2)**2;return 6371*2*atan2(sqrt(x),sqrt(1-x))
def execute(ctx,state,locations,a,b):
 d=define(ctx)
 if a not in locations or b not in locations:raise MechanicError('GAME_MECH_MAP_UNKNOWN_LOCATION')
 typed={name:SourcedMapLocation.from_mapping(name,row) for name,row in locations.items()}
 dist=round(_distance((typed[a].lat,typed[a].lon),(typed[b].lat,typed[b].lon)),3);after={**state,'selected_pair':(a,b),'distance_km':dist};out={'distance_km':dist,'source_refs':(typed[a].source_ref,typed[b].source_ref)};return after,out,receipt(d,state,after,{'from':a,'to':b},out)
