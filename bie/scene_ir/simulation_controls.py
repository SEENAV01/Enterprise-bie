from dataclasses import dataclass
from .interaction_common import *

@dataclass(frozen=True)
class SimulationControl:
    control_id:str
    simulation_element_id:str
    control_type:str
    state_path:str
    min_value:float|None=None
    max_value:float|None=None
    step:float|None=None
    options:tuple[str,...]=()
    requires_verified_execution:bool=False
    def __post_init__(self):
        object.__setattr__(self,"control_id",tok(self.control_id,"control_id"))
        object.__setattr__(self,"simulation_element_id",tok(self.simulation_element_id,"simulation_element_id"))
        object.__setattr__(self,"state_path",tok(self.state_path,"state_path"))
        if self.control_type not in {"slider","toggle","choice","button","scrubber","vector_input"}:
            raise InteractionIRError("unsupported control_type")
        if self.control_type=="slider":
            if self.min_value is None or self.max_value is None:
                raise InteractionIRError("slider requires min/max")
            lo,hi=finite(self.min_value,"min_value"),finite(self.max_value,"max_value")
            if hi<=lo: raise InteractionIRError("slider max must exceed min")
            object.__setattr__(self,"min_value",lo);object.__setattr__(self,"max_value",hi)
            if self.step is not None:
                st=finite(self.step,"step")
                if st<=0: raise InteractionIRError("step must be positive")
                object.__setattr__(self,"step",st)
        if self.control_type=="choice":
            opts=unique_ids(self.options,"options")
            object.__setattr__(self,"options",opts)

def validate_simulation_controls(controls, known_simulation_ids, known_state_paths, execution_class_by_sim):
    controls=tuple(controls); sims=set(known_simulation_ids); states=set(known_state_paths)
    if len({c.control_id for c in controls})!=len(controls):
        raise InteractionIRError("duplicate control_id")
    blockers=[]
    for c in controls:
        if c.simulation_element_id not in sims:
            blockers.append("unknown_simulation:"+c.control_id)
        if c.state_path not in states:
            blockers.append("unknown_state_path:"+c.control_id)
        if c.requires_verified_execution and execution_class_by_sim.get(c.simulation_element_id)!="verified_observed_execution":
            blockers.append("verified_execution_required:"+c.control_id)
    return tuple(sorted(set(blockers)))
