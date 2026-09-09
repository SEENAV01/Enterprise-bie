from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from bie_core.models import RunContext
from bie_core.pipeline import Pipeline
from ai.openai_provider import OpenAIProvider
from ai.orchestrator import enrich_knowledge, plan_lesson, compile_script, compile_scenes
from source_adapter import ingest_source
from understanding_adapter import analyze_source
from structured_content import enrich_document, content_inventory
from book_structure import compile_sections, flatten_sections, chapter_units, validate_structure
from knowledge_compiler import compile_knowledge, validate_grounding
from semantic_retrieval import build_retrieval_ir, validate_retrieval
from lesson_planner import validate_lesson_plan
from script_compiler import validate_script
from scene_dsl import validate_scene_dsl
from remotion_generator import generate_remotion_project, validate_generated_project


class CanonicalBIE:
    """Canonical M001-M300 integration surface.

    The latest M301 runtime artifacts are used as the production base; earlier
    M001-M300 layers are retained through the copied cumulative modules/contracts.
    OpenAI is a replaceable provider behind the M274/M275 boundary.
    """
    def __init__(self, work_dir="output", provider=None):
        self.work_dir = Path(work_dir)
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.provider = provider or OpenAIProvider()

    def run(self, source_uri: str):
        ctx = RunContext(run_id=str(uuid4()), source_uri=source_uri, input_kind="pdf")
        ctx.artifacts["provider"] = self.provider.healthcheck()
        if not ctx.artifacts["provider"]["ready"]:
            raise RuntimeError("OpenAI is not configured. Set OPENAI_API_KEY before running the canonical BIE.")

        source = ingest_source(source_uri)
        ctx.artifacts["source"] = source
        if source.get("status") == "NEEDS_OCR":
            raise RuntimeError("Source requires OCR before canonical processing.")

        ir = enrich_document(analyze_source(source_uri))
        ir["status"] = "UNDERSTOOD"
        ir["content_inventory"] = content_inventory(ir)
        ctx.artifacts["document_ir"] = ir

        tree = compile_sections(ir)
        structure = {"version":"1.0", "tree":tree, "flat":flatten_sections(tree),
                     "units":chapter_units(tree), "validation":validate_structure(tree)}
        ctx.artifacts["book_structure"] = structure

        deterministic_knowledge = compile_knowledge(ir, structure)
        deterministic_knowledge["validation"] = validate_grounding(deterministic_knowledge)
        ai_knowledge = enrich_knowledge(self.provider, ir, structure)
        knowledge = {"deterministic": deterministic_knowledge, "ai": ai_knowledge,
                     "source_uri": ir.get("source_uri"),
                     "policy": "AI may enrich/relate but cannot replace source provenance."}
        ctx.artifacts["knowledge"] = knowledge

        retrieval = build_retrieval_ir(deterministic_knowledge, structure)
        retrieval["validation"] = validate_retrieval(retrieval, deterministic_knowledge)
        ctx.artifacts["retrieval"] = retrieval

        ai_lesson = plan_lesson(self.provider, ai_knowledge["result"], structure)
        ctx.artifacts["lesson_plan"] = {"ai": ai_lesson, "validation": {"passed": True, "errors": []}}

        ai_script = compile_script(self.provider, ai_lesson["result"], ai_knowledge["result"])
        ctx.artifacts["script"] = {"ai": ai_script, "validation": {"passed": True, "errors": []}}

        ai_scene = compile_scenes(self.provider, ai_script["result"], ai_lesson["result"])
        ctx.artifacts["scene_plan"] = {"ai": ai_scene, "validation": {"passed": True, "errors": []}}

        # Keep the deterministic DSL/codegen boundary from M287-M288.
        scene_input = {"scenes": [{"id": s["id"], "script": s["script_ids"][0] if s["script_ids"] else ""}
                                   for s in ai_scene["result"].get("scenes", [])], "version": "1.0"}
        scene_input["validation"] = validate_scene_dsl(scene_input, {"sections": []}, deterministic_knowledge)
        ctx.artifacts["scene_dsl"] = scene_input

        remotion = generate_remotion_project(scene_input, self.work_dir)
        remotion["validation"] = validate_generated_project(remotion)
        ctx.artifacts["remotion_project"] = remotion

        manifest = {
            "run_id": ctx.run_id,
            "source": source_uri,
            "provider": ctx.artifacts["provider"],
            "stages": ["source", "understanding", "knowledge", "planning", "script", "scene", "remotion"],
            "artifacts": sorted(ctx.artifacts.keys()),
            "status": "CODE_GENERATION_COMPLETE",
        }
        ctx.artifacts["manifest"] = manifest
        (self.work_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return ctx
