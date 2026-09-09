PRIMITIVES={
 "text":{"supports":["fade","type","highlight","scale"]},
 "diagram":{"supports":["draw","highlight","pan","zoom","label_reveal","trace_path"]},
 "equation":{"supports":["write","transform","highlight_term","box_term","substitute","simplify"]},
 "chart":{"supports":["grow","draw_axis","highlight_series","focus_region"]},
 "table":{"supports":["reveal_row","reveal_column","highlight_cell","compare_rows"]},
 "process":{"supports":["step_reveal","flow","pulse","trace","branch"]},
 "simulation":{"supports":["parameter_change","particle_motion","field_lines","plot_update"]},
 "real_world":{"supports":["pan","zoom","focus","callout"]},
 "mixed":{"supports":["compose"]}
}

def validate_action(visual_type, action):
    allowed=PRIMITIVES.get(visual_type,{}).get("supports",[])
    return action in allowed
