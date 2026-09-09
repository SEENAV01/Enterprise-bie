from complexity import estimate_complexity
from quality import quality_profile,quality_score
from resources import resource_request
from render_strategy import choose_strategy
from quality_gate import evaluate
from semantic_profile import semantic_profile

def build_quality_aware():
    features={"concepts":5,"equations":3,"diagrams":4,
              "simulation":2,"3d":0,"code":0,"assets":5}
    semantic=semantic_profile(
        "Electric field simulation",features,
        "Understand field behavior through visual simulation","students")
    complexity=estimate_complexity(features)
    quality=quality_profile(complexity,"HIGH","HIGH","HIGH")
    resources=resource_request(complexity,quality)
    strategy=choose_strategy(complexity,features)
    gate=evaluate(strategy,complexity,quality)
    return {"schema_version":"6.68","semantic_profile":semantic,
            "complexity":complexity,"quality_profile":quality,
            "quality_score":quality_score(quality),
            "resource_request":resources,
            "render_strategy":strategy,
            "quality_gate":gate,
            "quality_aware_gate":{"valid":(
                complexity["level"]=="HIGH"
                and strategy["strategy"]=="HYBRID_2D_SIMULATION"
                and resources["gpu"]>=1
                and gate["passed"]
            ),"errors":[]}}
