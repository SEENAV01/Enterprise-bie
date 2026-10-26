"""Aggregate shot cards into a ranked 'what to build' list (needs list)."""
import json, glob, os, collections

HERE = os.path.dirname(os.path.abspath(__file__))
cards = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(HERE, "..", "shot_cards", "*.json")))]

GROUP = {  # recipe need -> (group, family)
    # stages / worlds
    "studio_grid_floor": ("stage", "studio stage (grid floor, gradient wall)"),
    "hardware_layout_floor": ("stage", "studio stage (grid floor, gradient wall)"),
    "desk_stage": ("stage", "desk / workbench stage"), "workbench_stage": ("stage", "desk / workbench stage"),
    "landscape_river_valley": ("stage", "landscape & water world"), "sea_surface": ("stage", "landscape & water world"),
    "museum_wall_gallery": ("stage", "gallery wall"),
    # model families
    "cell_sheet_organic": ("model", "cell & tissue family"), "cell_sheet_on_curve": ("model", "cell & tissue family"),
    "microvilli_brush": ("model", "cell & tissue family"), "acinus_radial": ("model", "cell & tissue family"),
    "duct_ring_cross_section": ("model", "cell & tissue family"), "tube_wall_cutaway": ("model", "organ & tube family"),
    "alveolus_capillary": ("model", "organ & tube family"), "capillary_context": ("model", "organ & tube family"),
    "rbc_flow": ("model", "cell & tissue family"), "chromosome_model": ("model", "cell & tissue family"),
    "centrosome_model": ("model", "cell & tissue family"), "cell_spindle_model": ("model", "cell & tissue family"),
    "exploded_view": ("motion", "exploded view / layer stack"), "layer_stack_cutaway": ("motion", "exploded view / layer stack"),
    "reassemble_animation": ("motion", "exploded view / layer stack"),
    "earth_cutaway": ("model", "earth & globe family"), "earth_wedge_cutaway": ("model", "earth & globe family"),
    "earth_globe": ("model", "earth & globe family"),
    "cad_part_model": ("model", "machine part family (CAD)"), "thread_bolt_model": ("model", "machine part family (CAD)"),
    "construction_machine_model": ("model", "construction machines & structures"), "cofferdam_ring": ("model", "construction machines & structures"),
    "barge_pontoon": ("model", "construction machines & structures"), "rebar_cage": ("model", "construction machines & structures"),
    "weir_structure": ("model", "construction machines & structures"), "parametric_zigzag_wall": ("model", "construction machines & structures"),
    "photoreal_prop_model": ("model", "photoreal props (motor, drone, rods)"), "product_material": ("look", "product-shot materials"),
    "chip_die_model": ("model", "electronics hardware family"), "hdd_model": ("model", "electronics hardware family"),
    "diamond_grid": ("model", "electronics hardware family"), "rgb_subpixel_grid": ("model", "electronics hardware family"),
    "water_tank_section": ("model", "water tank / fluid section"),
    "charge_sphere": ("model", "physics primitives (charges, magnets, rings)"), "bar_magnet": ("model", "physics primitives (charges, magnets, rings)"),
    "spinning_charge_ring": ("model", "physics primitives (charges, magnets, rings)"),
    # looks / materials
    "sss_translucent_material": ("look", "translucent tissue material (SSS)"), "glass_cell_material": ("look", "translucent tissue material (SSS)"),
    "glass_material": ("look", "glass & water materials"), "water_surface_material": ("look", "glass & water materials"),
    "glass_globe_material": ("look", "glass & water materials"), "glass_panel": ("look", "glass graph panel"),
    "paper_sheet_material": ("look", "paper & line-drawing look"), "dof_bokeh": ("look", "depth of field + bokeh"),
    "focus_glow_outline": ("look", "focus glow / highlight outline"), "highlight_outline": ("look", "focus glow / highlight outline"),
    "region_highlight": ("look", "focus glow / highlight outline"), "bloom": ("look", "emissive glow / bloom"),
    "emission_glow": ("look", "emissive glow / bloom"), "neon_outline_view": ("look", "neon outline drawing"),
    "voronoi_cell_outlines": ("look", "focus glow / highlight outline"),
    # motion
    "particle_flow_across": ("motion", "particle flow (across, along a path, burst)"), "particle_stream_path": ("motion", "particle flow (across, along a path, burst)"),
    "particle_burst_release": ("motion", "particle flow (across, along a path, burst)"), "charge_particles": ("motion", "particle flow (across, along a path, burst)"),
    "ion_swap_particles": ("motion", "particle flow (across, along a path, burst)"), "particle_count_change": ("motion", "particle flow (across, along a path, burst)"),
    "rain_particles": ("motion", "particle flow (across, along a path, burst)"),
    "flow_arrows": ("motion", "flow arrows"), "field_arcs": ("motion", "field lines & vector arrows"),
    "radial_field_lines": ("motion", "field lines & vector arrows"), "dipole_field_lines": ("motion", "field lines & vector arrows"),
    "magnetic_field_loops": ("motion", "field lines & vector arrows"), "vector_arrow_field": ("motion", "field lines & vector arrows"),
    "triad_arrows_3d": ("motion", "field lines & vector arrows"), "vector_arrows_2d": ("motion", "field lines & vector arrows"),
    "ripple_rings": ("motion", "ripple / pulse rings"), "sonar_pulse": ("motion", "ripple / pulse rings"),
    "water_level_change": ("motion", "fluid motion (level, pour, flow)"), "concrete_pour_fluid": ("motion", "fluid motion (level, pour, flow)"),
    "pile_drive_motion": ("motion", "machine actions (drive, dig, lower, grow)"), "excavator_dig_motion": ("motion", "machine actions (drive, dig, lower, grow)"),
    "crane_lowering": ("motion", "machine actions (drive, dig, lower, grow)"), "pipe_lowering": ("motion", "machine actions (drive, dig, lower, grow)"),
    "structure_grow_up": ("motion", "machine actions (drive, dig, lower, grow)"), "interlock_assembly": ("motion", "machine actions (drive, dig, lower, grow)"),
    "cutaway_section": ("motion", "cutaway / cross-section"), "terrain_cross_section": ("motion", "cutaway / cross-section"),
    "cylinder_cutaway": ("motion", "cutaway / cross-section"), "water_volume_cutaway": ("motion", "cutaway / cross-section"),
    "section_hatching": ("motion", "cutaway / cross-section"),
    "organ_zoom": ("camera", "zoom from organ / macro zoom"), "macro_zoom_into_surface": ("camera", "zoom from organ / macro zoom"),
    "orbit_camera": ("camera", "orbit & glide camera"), "camera_glide": ("camera", "orbit & glide camera"),
    "aerial_camera_path": ("camera", "aerial / tracking path"), "tracking_camera": ("camera", "aerial / tracking path"),
    "projection_plane": ("motion", "projection planes & unfolding"), "unfold_box_animation": ("motion", "projection planes & unfolding"),
    "layout_unfold": ("motion", "projection planes & unfolding"),
    "scale_compare": ("motion", "scale comparison & instanced arrays"), "instanced_array": ("motion", "scale comparison & instanced arrays"),
    "distance_metaphor_line": ("motion", "scale comparison & instanced arrays"), "measure_line": ("motion", "scale comparison & instanced arrays"),
    # 2D / text
    "graph_plot": ("2d", "graph plotting"), "linked_graph_panels": ("2d", "graph plotting"), "tangent_slide": ("2d", "graph plotting"),
    "secant_to_tangent": ("2d", "graph plotting"), "area_under_curve": ("2d", "graph plotting"), "point_markers": ("2d", "graph plotting"),
    "equation_steps": ("2d", "equation steps & annotation"), "equation_part_boxes": ("2d", "equation steps & annotation"),
    "equation_annotation": ("2d", "equation steps & annotation"), "formula_table_panel": ("2d", "equation steps & annotation"),
    "leader_label": ("text", "leader-line labels"), "callout_tag": ("text", "tags, title blocks & callouts"),
    "tag_label": ("text", "tags, title blocks & callouts"), "title_tag": ("text", "tags, title blocks & callouts"),
    "floating_title_block": ("text", "tags, title blocks & callouts"), "location_pin": ("text", "tags, title blocks & callouts"),
    "dimension_lines": ("text", "dimension lines"), "dimension_label": ("text", "dimension lines"),
    "kinetic_caption": ("text", "kinetic caption + summary line"), "summary_line": ("text", "kinetic caption + summary line"),
    "line_drawing_draw_on": ("2d", "line drawing draw-on"), "free_body_diagram": ("2d", "free-body & vector diagrams (2D)"),
    "split_compare": ("2d", "split compare & tables"), "tick_cross_table": ("2d", "split compare & tables"),
    "rating_table_3d": ("2d", "split compare & tables"),
}

need_videos = collections.defaultdict(set); need_sec = collections.Counter(); need_cards = collections.Counter()
fam_videos = collections.defaultdict(set); fam_sec = collections.Counter(); fam_needs = collections.defaultdict(set)
level_sec = collections.Counter(); cam = collections.Counter(); trans = collections.Counter(); labels = collections.Counter()
unmapped = collections.Counter()
for v in cards:
    for c in v["shots"]:
        s = max(c["seconds"], 1)
        level_sec[c["level"]] += s
        if c["level"] in ("L1",) or "promo" in c.get("notes", "") or "branding" in c.get("notes", ""):
            continue
        cam[c["camera"]["movement"]] += s; trans[c["camera"]["transition_in"]] += 1
        labels[c["on_screen_text"]["label_style"]] += 1
        for n in c["recipe_needs"]:
            need_videos[n].add(v["id"]); need_sec[n] += s; need_cards[n] += 1
            g = GROUP.get(n)
            if g:
                fam = g[0] + " | " + g[1]
                fam_videos[fam].add(v["id"]); fam_sec[fam] += s; fam_needs[fam].add(n)
            else:
                unmapped[n] += 1

rows = sorted(fam_sec, key=lambda f: (-len(fam_videos[f]), -fam_sec[f]))
out = {"videos": len(cards), "cards": sum(len(v["shots"]) for v in cards),
       "level_seconds": dict(level_sec), "camera_movement_seconds": dict(cam.most_common()),
       "transitions": dict(trans.most_common()), "label_styles": dict(labels.most_common()),
       "families": [{"family": f, "videos": len(fam_videos[f]), "seconds": fam_sec[f],
                     "video_ids": sorted(fam_videos[f]), "needs": sorted(fam_needs[f])} for f in rows],
       "unmapped_needs": dict(unmapped.most_common())}
json.dump(out, open(os.path.join(HERE, "..", "needs_list.json"), "w"), indent=1)
print("videos", out["videos"], "cards", out["cards"])
print("levels", out["level_seconds"])
print("camera", dict(cam.most_common(8)))
print("transitions", out["transitions"])
for r in out["families"]:
    print(f'{r["videos"]:2d} vids {r["seconds"]:5d}s  {r["family"]}')
print("unmapped", out["unmapped_needs"])
