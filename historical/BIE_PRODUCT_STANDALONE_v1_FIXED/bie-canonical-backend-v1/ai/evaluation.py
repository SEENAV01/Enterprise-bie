def evaluation_record(prompt_version, output, criteria):
    scores={k:criteria[k](output) for k in criteria}
    return {"prompt_version":prompt_version,"scores":scores,
            "passed":all(bool(v) for v in scores.values())}

def version_diff(a,b):
    return {"template_changed":a["template"]!=b["template"],
            "variables_changed":a["variables"]!=b["variables"],
            "schema_changed":a.get("output_schema")!=b.get("output_schema")}
