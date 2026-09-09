from evaluator import evaluate_course
from quality_gate import quality_gate

def compile_qa(scenes,render_results=None,reviews=None):
    evaluation=evaluate_course(scenes)
    gate=quality_gate(evaluation["scene_results"],render_results,reviews)
    return {"schema_version":"5.16","evaluation":evaluation,
            "render_validation":render_results or [],
            "human_review":reviews or [],
            "quality_gate":gate}
