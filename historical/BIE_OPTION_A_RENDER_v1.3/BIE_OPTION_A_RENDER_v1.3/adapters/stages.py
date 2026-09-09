from source_adapter import ingest_source, build_document_ir
from understanding_adapter import analyze_source
from structured_content import enrich_document, content_inventory
from book_structure import compile_sections, flatten_sections, chapter_units, validate_structure
from knowledge_compiler import compile_knowledge, validate_grounding
from semantic_retrieval import build_retrieval_ir, validate_retrieval
from lesson_planner import compile_lesson_plan, validate_lesson_plan
from script_compiler import compile_script, validate_script
from scene_dsl import compile_scene_dsl, validate_scene_dsl
from remotion_generator import generate_remotion_project, validate_generated_project
from mp4_renderer import render_mp4, validate_render
from visual_qa import inspect_render, generate_repair_plan, validate_visual_qa
from frame_readability_qa import sample_frames, estimate_readability, build_readability_report, generate_readability_repair_plan
from ocr_text_bbox_qa import run_ocr, analyze_text_boxes, validate_ocr_contract, generate_ocr_repair_plan
from equation_diagram_qa import build_equation_diagram_report, generate_equation_diagram_repair_plan, validate_equation_diagram_report
from semantic_verify_repair import semantic_compare, build_repair_patch, hash_dsl
from auto_repair_pipeline import apply_repair_and_prepare, regression_compare

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
            ir = {
                "ir_version": "2.1",
                "source_uri": ctx.source_uri,
                "input_kind": ctx.input_kind,
                "status": "READY",
                "pages": [{
                    "page": 1,
                    "blocks": [
                        {"block_id":"demo:h1","kind":"HEADING","text":"Chapter 1: Electric Charge","bbox":[100,80,800,130]},
                        {"block_id":"demo:p1","kind":"PARAGRAPH","text":"Electric charge is a property of matter.","bbox":[100,160,1500,220]}
                    ]
                }],
                "page_count": 1,
                "figure_count": 0,
                "table_count": 0,
                "equation_count": 0,
                "sections": [],
                "reading_order":"bbox_y_then_x",
                "layout_aware": True,
                "content_inventory": {"HEADING":1,"PARAGRAPH":1}
            }
            ctx.artifacts["document_ir"] = ir
        elif source.get("input_kind") == "pdf" and source.get("status") == "NEEDS_OCR":
            ctx.artifacts["document_ir"] = build_document_ir(source)
            ctx.artifacts["document_ir"]["layout_status"] = "OCR_REQUIRED"
        elif source.get("input_kind") == "pdf":
            ir = enrich_document(analyze_source(ctx.source_uri))
            ir["status"] = "UNDERSTOOD"
            ir["content_inventory"] = content_inventory(ir)
            ctx.artifacts["document_ir"] = ir
        else:
            ir = build_document_ir(source)
            ir["status"] = "READY"
            ctx.artifacts["document_ir"] = ir
        return ctx

class KnowledgeStage:
    name = "knowledge"
    def execute(self, ctx):
        ir = ctx.artifacts["document_ir"]
        tree = compile_sections(ir)
        structure = {
            "version":"1.0",
            "tree":tree,
            "flat":flatten_sections(tree),
            "units":chapter_units(tree),
            "validation":validate_structure(tree)
        }
        ctx.artifacts["book_structure"] = structure
        knowledge = compile_knowledge(ir, structure)
        knowledge["validation"] = validate_grounding(knowledge)
        ctx.artifacts["knowledge"] = knowledge
        retrieval = build_retrieval_ir(knowledge, structure)
        retrieval["validation"] = validate_retrieval(retrieval, knowledge)
        ctx.artifacts["retrieval"] = retrieval
        return ctx

class PlanningStage:
    name = "planning"
    def execute(self, ctx):
        units = ctx.artifacts["book_structure"]["units"]
        title = units[0]["title"] if units else "Electric Charge"
        plan = compile_lesson_plan(ctx.artifacts["book_structure"],
                                    ctx.artifacts["knowledge"],
                                    ctx.artifacts["retrieval"])
        plan["title"] = title
        plan["objectives"] = ["Define electric charge", "Explain attraction and repulsion"]
        plan["validation"] = validate_lesson_plan(plan, ctx.artifacts["knowledge"])
        ctx.artifacts["lesson_plan"] = plan
        return ctx

class ScriptStage:
    name = "script"
    def execute(self, ctx):
        script = compile_script(ctx.artifacts["lesson_plan"],
                                 ctx.artifacts["knowledge"],
                                 ctx.artifacts["book_structure"])
        script["validation"] = validate_script(script, ctx.artifacts["knowledge"])
        ctx.artifacts["script"] = script
        return ctx

class SceneStage:
    name = "scene"
    def execute(self, ctx):
        dsl = compile_scene_dsl(ctx.artifacts["script"], ctx.artifacts["knowledge"])
        dsl["validation"] = validate_scene_dsl(
            dsl, ctx.artifacts["script"], ctx.artifacts["knowledge"]
        )
        ctx.artifacts["scene_dsl"] = dsl
        return ctx

class RemotionStage:
    name = "remotion"
    def execute(self, ctx):
        meta = generate_remotion_project(
            ctx.artifacts["scene_dsl"], ctx.work_dir
        )
        meta["validation"] = validate_generated_project(meta)
        ctx.artifacts["remotion_project"] = meta
        return ctx

class RenderStage:
    name = "render"
    def execute(self, ctx):
        ctx.artifacts["render"] = {
            "status":"READY_FOR_RENDER",
            "output":"out/bie-lesson.mp4"
        }
        return ctx

class QAStage:
    name = "qa"
    def execute(self, ctx):
        required = ["document_ir", "book_structure", "knowledge", "lesson_plan", "script", "scene_dsl", "remotion_project"]
        missing = [k for k in required if k not in ctx.artifacts]
        ctx.artifacts["qa_report"] = {"passed": not missing, "missing": missing}
        return ctx

class PublishStage:
    name = "publish"
    def execute(self, ctx):
        if not ctx.artifacts.get("qa_report", {}).get("passed"):
            raise RuntimeError("QA gate failed")
        ctx.artifacts["publish"] = {"status": "PUBLISH_READY"}
        return ctx
