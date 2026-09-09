def equation_plan(equation, reveal_steps=None):
    return {
        "source":equation,
        "renderer":"latex",
        "reveal_steps":reveal_steps or [equation],
        "sync_mode":"MARKER_DRIVEN"
    }

def validate_equation(eq):
    return bool(eq.get("source")) and eq.get("renderer")=="latex"
