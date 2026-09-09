class SourceStage:
    name = "source"
    def execute(self, ctx):
        ctx.artifacts["source"] = {"uri": ctx.source_uri, "kind": ctx.input_kind}
        return ctx

class UnderstandingStage:
    name = "understanding"
    def execute(self, ctx):
        ctx.artifacts["document_ir"] = {
            "source_uri": ctx.source_uri,
            "status": "READY",
            "pages": 1
        }
        return ctx

class KnowledgeStage:
    name = "knowledge"
    def execute(self, ctx):
        ctx.artifacts["knowledge"] = {
            "entities": ["electric charge"],
            "relations": [],
            "evidence": ["document_ir"]
        }
        return ctx

class PlanningStage:
    name = "planning"
    def execute(self, ctx):
        ctx.artifacts["lesson_plan"] = {
            "title": "Electric Charge",
            "objectives": ["Define electric charge", "Explain attraction and repulsion"]
        }
        return ctx

class ScriptStage:
    name = "script"
    def execute(self, ctx):
        ctx.artifacts["script"] = {
            "sections": [
                {"id": "s1", "text": "Electric charge is a property of matter."},
                {"id": "s2", "text": "Like charges repel and unlike charges attract."}
            ]
        }
        return ctx

class SceneStage:
    name = "scene"
    def execute(self, ctx):
        ctx.artifacts["scene_dsl"] = {
            "version": "1.0",
            "scenes": [
                {"id": "scene-1", "script": "s1"},
                {"id": "scene-2", "script": "s2"}
            ]
        }
        return ctx

class RemotionStage:
    name = "remotion"
    def execute(self, ctx):
        ctx.artifacts["remotion_project"] = {
            "entry": "remotion/src/Root.tsx",
            "composition_id": "BIELesson"
        }
        return ctx

class RenderStage:
    name = "render"
    def execute(self, ctx):
        # Adapter boundary: production implementation invokes Remotion CLI/service.
        ctx.artifacts["render"] = {
            "status": "READY_FOR_RENDER",
            "output": "out/bie-lesson.mp4"
        }
        return ctx

class QAStage:
    name = "qa"
    def execute(self, ctx):
        required = ["document_ir","knowledge","lesson_plan","script",
                    "scene_dsl","remotion_project","render"]
        missing = [k for k in required if k not in ctx.artifacts]
        ctx.artifacts["qa_report"] = {
            "passed": not missing,
            "missing": missing,
            "checks": ["traceability", "required-stage-artifacts"]
        }
        return ctx

class PublishStage:
    name = "publish"
    def execute(self, ctx):
        if not ctx.artifacts["qa_report"]["passed"]:
            raise RuntimeError("QA gate failed")
        ctx.artifacts["publish"] = {
            "status": "PUBLISH_READY",
            "video": ctx.artifacts["render"]["output"]
        }
        return ctx
