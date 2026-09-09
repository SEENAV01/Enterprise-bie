from .models import RunContext
from .pipeline import Pipeline
from .gates import RequiredArtifactGate
from adapters.stages import (
    SourceStage, UnderstandingStage, KnowledgeStage, PlanningStage,
    ScriptStage, SceneStage, RemotionStage, RenderStage, QAStage, PublishStage
)

def build_pipeline():
    stages = [
        SourceStage(), UnderstandingStage(), KnowledgeStage(),
        PlanningStage(), ScriptStage(), SceneStage(),
        RemotionStage(), RenderStage(), QAStage(), PublishStage()
    ]
    gates = {
        "source": [RequiredArtifactGate("SourceGate", "source")],
        "understanding": [RequiredArtifactGate("UnderstandingGate", "document_ir")],
        "knowledge": [RequiredArtifactGate("KnowledgeGate", "knowledge")],
        "planning": [RequiredArtifactGate("PlanningGate", "lesson_plan")],
        "script": [RequiredArtifactGate("ScriptGate", "script")],
        "scene": [RequiredArtifactGate("SceneGate", "scene_dsl")],
        "remotion": [RequiredArtifactGate("RemotionGate", "remotion_project")],
        "render": [RequiredArtifactGate("RenderGate", "render")],
        "qa": [RequiredArtifactGate("QAGate", "qa_report")],
    }
    return Pipeline(stages, gates)

def run(source_uri="example://electric-charge"):
    ctx = RunContext(run_id="m278-demo-001", source_uri=source_uri)
    return build_pipeline().run(ctx)
