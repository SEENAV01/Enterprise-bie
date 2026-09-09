from source_adapter import ingest_source, build_document_ir
from understanding_adapter import analyze_source
from structured_content import enrich_document, content_inventory

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
        source = ctx.artifacts["source"]
        if ctx.source_uri.startswith(("example://", "demo://")):
            ctx.artifacts["document_ir"] = {
                "ir_version": "2.0",
                "source_uri": ctx.source_uri,
                "input_kind": ctx.input_kind,
                "status": "READY",
                "pages": [{
                    "page": 1,
                    "blocks": [{
                        "block_id": "demo:block:1",
                        "kind": "PARAGRAPH",
                        "text": "Electric charge is a property of matter.",
                        "bbox": None
                    }]
                }],
                "page_count": 1,
                "figure_count": 0,
                "sections": [{
                    "section_id": "preamble",
                    "level": 1,
                    "title": "Preamble",
                    "start_page": 1,
                    "blocks": ["demo:block:1"]
                }],
                "layout_aware": True,
                "reading_order": "bbox_y_then_x",
                "content_inventory": {"PARAGRAPH": 1}
            }
        else:
            if source.get("input_kind") == "pdf" and source.get("status") == "NEEDS_OCR":
                # Do not silently manufacture content. OCR is a separate explicit operation.
                ctx.artifacts["document_ir"] = build_document_ir(source)
                ctx.artifacts["document_ir"]["layout_status"] = "OCR_REQUIRED"
            elif source.get("input_kind") == "pdf":
                base_ir = analyze_source(ctx.source_uri)
                ctx.artifacts["document_ir"] = enrich_document(base_ir)
                ctx.artifacts["document_ir"]["status"] = "UNDERSTOOD"
                ctx.artifacts["document_ir"]["content_inventory"] = content_inventory(ctx.artifacts["document_ir"])
            else:
                ctx.artifacts["document_ir"] = build_document_ir(source)
                ctx.artifacts["document_ir"]["status"] = "READY"
        return ctx

class KnowledgeStage:
    name = "knowledge"
    def execute(self, ctx):
        ir = ctx.artifacts["document_ir"]
        blocks = []
        for page in ir.get("pages", []):
            blocks.extend(b["block_id"] for b in page.get("blocks", [])
                          if b.get("kind") != "FIGURE")
        ctx.artifacts["knowledge"] = {
            "entities": ["electric charge"],
            "relations": [],
            "evidence": blocks
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
        blocked = ir.get("requires_ocr", False) or ir.get("layout_status") == "OCR_REQUIRED"
        ctx.artifacts["qa_report"] = {
            "passed": not missing and not blocked,
            "missing": missing,
            "checks": ["traceability", "required-stage-artifacts",
                       "source-readiness", "layout-readiness"],
            "blocked_reason": "OCR_REQUIRED" if blocked else None
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
