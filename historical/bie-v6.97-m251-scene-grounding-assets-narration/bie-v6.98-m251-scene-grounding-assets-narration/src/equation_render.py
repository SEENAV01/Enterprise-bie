def render_equation(expression, display_mode="math"):
    return {"expression":expression,"display_mode":display_mode,
            "render_key":expression.replace(" ","_")}

def validate_equation_render(rendered, expected_expression):
    return {"valid":rendered.get("expression")==expected_expression,
            "errors":[] if rendered.get("expression")==expected_expression else ["EQUATION_MISMATCH"]}
