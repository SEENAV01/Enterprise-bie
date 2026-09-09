from templates import register_template,render_template
from context import assemble_context,grounded_context
from budget import fit_token_budget
from output import validate_structured_output,normalize_output
from evaluation import evaluation_record,version_diff

def build_m275_runtime():
    registry={}
    v1=register_template(registry,"lesson-planner","v1",
        "Create a lesson from {topic}. Use the supplied sources: {context}.",
        ["topic","context"],{"required":["title","objectives"]})
    v2=register_template(registry,"lesson-planner","v2",
        "Create a rigorous lesson from {topic}. Ground every claim in: {context}.",
        ["topic","context"],{"required":["title","objectives"]})
    sources=["source:chapter-1","source:chapter-2","source:chapter-3"]
    context=assemble_context(sources)
    grounded=grounded_context(context["items"],["source:chapter-1","source:chapter-2"])
    bounded=fit_token_budget(["topic: electric charge"]+context["items"],5)
    rendered=render_template(v2,{"topic":"electric charge","context":grounded["sources"]})
    output=normalize_output({"title":"Electric Charge","objectives":["Define charge"]})
    validation=validate_structured_output(output,["title","objectives"])
    evaluation=evaluation_record("lesson-planner:v2",output,{"has_title":lambda x:"title" in x,
                                                              "has_objectives":lambda x:bool(x.get("objectives"))})
    return {"schema_version":"7.22","templates":[v1,v2],
            "context":{"assembled":context,"grounded":grounded},
            "token_budget":bounded,"rendered_prompt":rendered,
            "structured_output":{"value":output,"validation":validation},
            "evaluation":evaluation,"version_diff":version_diff(v1,v2),
            "prompt_context_gate":{"valid":validation["valid"] and evaluation["passed"] and
                                  bounded["used"]<=bounded["budget"],"errors":[]}}
