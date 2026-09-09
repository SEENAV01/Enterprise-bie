def register_template(store, template_id, version, template, variables, output_schema=None):
    key=f"{template_id}:{version}"
    item={"template_id":template_id,"version":version,"template":template,
          "variables":list(variables),"output_schema":output_schema,"status":"ACTIVE"}
    store[key]=item
    return item

def render_template(template, bindings):
    return template.format(**bindings)
