def animation_plan(duration_policy="CONTENT_DRIVEN",
                   entrance=None,transitions=None,
                   emphasis=None,exit=None):
    return {"duration_policy":duration_policy,"entrance":entrance or [],
            "transitions":transitions or [],
            "emphasis":emphasis or [],
            "exit":exit or []}
