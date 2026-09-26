from fractions import Fraction
from .common import *
def define(ctx):return make_definition(ctx,'mechanic:equation',MechanicKind.EQUATION_BALANCE,'Learner preserves equation invariants while applying explicit symbolic operations to both sides.',(action('adjust:equation',ActionKind.ADJUST,'Apply operation to both sides','Arrow keys then Enter','equation:balance'),),(motion('motion:balance',MotionSemantic.BALANCE,'equation:balance','Show invariant preservation across both sides.','equation_state'),),('semantic_motion','keyboard_input','state_machine','equation'))
def execute(ctx,state,lhs,rhs,operation,value):
 d=define(ctx);lhs=Fraction(lhs);rhs=Fraction(rhs);v=Fraction(value)
 if operation not in {'add','sub','mul','div'}:raise MechanicError('GAME_MECH_EQUATION_OPERATION')
 if operation=='div' and v==0:raise MechanicError('GAME_MECH_EQUATION_DIV_ZERO')
 fn={'add':lambda x:x+v,'sub':lambda x:x-v,'mul':lambda x:x*v,'div':lambda x:x/v}[operation];nl,nr=fn(lhs),fn(rhs);balanced_before=lhs==rhs;balanced_after=nl==nr
 if balanced_before!=balanced_after:raise MechanicError('GAME_MECH_EQUATION_INVARIANT')
 after={**state,'lhs':str(nl),'rhs':str(nr),'balanced':balanced_after};out={'operation':operation,'value':str(v),'invariant_preserved':True};return after,out,receipt(d,state,after,{'operation':operation,'value':str(v)},out)
