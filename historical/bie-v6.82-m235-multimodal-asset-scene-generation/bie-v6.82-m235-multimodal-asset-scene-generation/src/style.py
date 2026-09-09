def visual_style(preferences,subject="educational"):
    density=preferences.get("visual_density","balanced")
    return {"subject":subject,"density":density,
            "contrast":"high" if preferences.get("high_contrast") else "standard",
            "motion":"reduced" if preferences.get("reduced_motion") else "standard",
            "layout":"spacious" if density=="low" else ("dense" if density=="high" else "balanced")}

def style_constraints(style):
    return {"density":style["density"],"contrast":style["contrast"],
            "motion":style["motion"],"layout":style["layout"]}
