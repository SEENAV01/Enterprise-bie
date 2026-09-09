def simulation(sim_id,variables,parameters,equations,
               initial_state,dt,steps):
    return {
      "simulation_id":sim_id,"variables":variables,
      "parameters":parameters,"equations":equations,
      "initial_state":initial_state,"dt":dt,"steps":steps,
      "integrator":"DECLARED_BY_BACKEND"
    }

def simulation_semantics(sim_id,observables,visual_mappings):
    return {
      "simulation_id":sim_id,"observables":observables,
      "visual_mappings":visual_mappings
    }
