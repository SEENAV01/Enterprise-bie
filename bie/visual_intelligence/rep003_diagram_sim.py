from .representation_core import *
def choose(intent,target,parameter_exploration=False,mechanism_states=1,simulation_model_evidence=False):
 if isinstance(mechanism_states,bool) or not isinstance(mechanism_states,int) or mechanism_states<1:raise RepresentationError('mechanism_states')
 sim=(.35 if intent.dynamic else 0)+(.25 if parameter_exploration else 0)+(.20 if mechanism_states>2 else 0)+(.20 if simulation_model_evidence else 0);dia=.55+(.20 if not intent.dynamic else 0)+(.15 if mechanism_states<=2 else 0)
 if sim>dia:
  if not target.supports_simulation:return decision(intent,'diagram','REVIEW',min(.85,dia),('simulation_more_explanatory_but_target_unsupported','diagram_fallback'),{'simulation_value':sim,'diagram_value':dia},'diagram-sim')
  if not simulation_model_evidence:return decision(intent,None,'REVIEW',.45,('simulation_requires_model_evidence',),{'simulation_value':sim},'diagram-sim')
  return decision(intent,'simulation','PASS',min(1,sim),('dynamic_exploration_justifies_simulation',),{'simulation_value':sim,'diagram_value':dia},'diagram-sim')
 return decision(intent,'diagram','PASS',min(1,dia),('static_structure_or_low_dynamic_gain',),{'simulation_value':sim,'diagram_value':dia},'diagram-sim')
