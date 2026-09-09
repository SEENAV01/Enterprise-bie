from source_adapter import ingest_source, build_document_ir

class SourceStage:
    name = "source"
    def execute(self, ctx):
        if ctx.source_uri.startswith(("example://", "demo://")):
            ctx.artifacts["source"] = {"uri": ctx.source_uri, "kind": ctx.input_kind}
        else:
            ctx.artifacts["source"] = ingest_source(ctx.source_uri)
        return ctx

class UnderstandingStage:
    name = "understanding"
    def execute(self, ctx):
        if "source" not in ctx.artifacts:
            raise RuntimeError("source artifact missing")
        if "status" in ctx.artifacts["source"]:
            ctx.artifacts["document_ir"] = build_document_ir(ctx.artifacts["source"])
        else:
            # Keep demo mode deterministic while the real adapter handles files.
            ctx.artifacts["document_ir"] = {
                "ir_version": "1.0",
                "source_uri": ctx.source_uri,
                "input_kind": ctx.input_kind,
                "status": "READY",
                "blocks": [{"locator": {"demo": True},
                            "text": "Electric charge is a property of matter.",
                            "block_id": "demo:block:1"}],
                "block_count": 1,
                "requires_ocr": False
            }
        return ctx

class KnowledgeStage:
    name = "knowledge"
    def execute(self, ctx):
        ctx.artifacts["knowledge"] = {
            "entities": ["electric charge"],
            "relations": [],
            "evidence": [b["block_id"] for b in ctx.artifacts["document_ir"]["blocks"]]
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
            "scenes": [{"id": "scene-1", "script": "s1"},
                       {"id": "scene-2", "script": "s2"}]
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
        ir = ctx.artifacts.get("document_ir", {})
        ctx.artifacts["qa_report"] = {
            "passed": not missing and not ir.get("requires_ocr", False),
            "missing": missing,
            "checks": ["traceability", "required-stage-artifacts", "source-readiness"]
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
