from factuality import claim
from definitions import definition
from formulas import formula
from content_qa import run_content_qa

def build_content_qa_runtime():
    claims=[claim("C1","Electric charge is a physical property.",
                  ["textbook:chapter1"],0.98)]
    definitions=[definition("electric field",
        "Electric field is force per unit positive test charge.",
        ["force","unit","charge"])]
    formulas=[formula("F1","F=q*E",
        ["F","q","E"],{"F":"N","q":"C","E":"N/C"})]
    qa=run_content_qa(claims,definitions,formulas,True)
    return {"schema_version":"6.85","claims":claims,"definitions":definitions,
            "formulas":formulas,"content_qa":qa,
            "content_quality_gate":{"valid":qa["passed"],"errors":[] if qa["passed"] else ["QA_FAILURE"]}}
