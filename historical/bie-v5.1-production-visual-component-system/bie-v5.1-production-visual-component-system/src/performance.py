def performance_policy():
    return {
      "prefer_vector_for_simple_shapes":True,
      "prefer_canvas_or_svg_for_large_static_diagrams":True,
      "cap_particle_count_by_scene":True,
      "avoid_unbounded_dom_growth":True,
      "memoize_static_assets":True,
      "precompute_expensive_geometry":True
    }
