"""QA-only integration adapter over the unchanged Scene IR/compiler emitters.

This assembles real generated projects for regression; it is not a replacement
production orchestrator or a claim of autonomous book-to-lesson generation.
Unconsumed contracts and nonexecuting animations remain explicit blockers.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Mapping
from .qa_common import CompilerQAError, QAFinding, digest, ordered_findings
from .artifact_hashing import canonical_json
from .scene_ir_loader import load_scene_ir_payload
from .react_project_emitter import emit_react_project
from .root_emitter import emit_root
from .composition_emitter import emit_composition
from .scene_component_emitter import emit_scene_component
from .react_emitter_common import emitted_file
from .deterministic_codegen import CodegenPlan, plan_deterministic_codegen
from .deterministic_output_qa import DeterminismContext
from .compile_diagnostics_mapping import SourceOrigin, GeneratedSourceSpan, GeneratedSourceMap, build_source_map
from .capability_fallback_qa import CapabilityFallbackQAReceipt, evaluate_capability_fallbacks
from .animation_track_compiler import compile_animation_track
from .text_compiler import compile_text_element
from .equation_compiler import compile_equation_element
from .graph_compiler import compile_graph_element
from .chart_compiler import compile_chart_element
from .map_compiler import compile_map_element
from .timeline_compiler import compile_timeline_element
from .model2d_compiler import compile_model2d_element
from .model3d_compiler import compile_model3d_element
from .vector_compiler import compile_vector_element
from .simulation_compiler import compile_simulation_element
from .particle_compiler import compile_particle_element
from .media_compiler import compile_image_or_video_element
from .annotation_callout_compiler import compile_annotation_callout_element
from .element_compiler_common import component_name, jsx
from bie.scene_ir.compiler_capability_declarations import CapabilityRegistry, CompilerCapability

EMITTERS = {
    "text": compile_text_element, "equation": compile_equation_element,
    "graph": compile_graph_element, "chart": compile_chart_element,
    "map": compile_map_element, "timeline": compile_timeline_element,
    "model2d": compile_model2d_element, "model3d": compile_model3d_element,
    "vector": compile_vector_element, "simulation": compile_simulation_element,
    "particle_system": compile_particle_element, "image": compile_image_or_video_element,
    "video": compile_image_or_video_element, "annotation": compile_annotation_callout_element,
    "callout": compile_annotation_callout_element,
}

@dataclass(frozen=True)
class CompilerQATarget:
    width: int = 640
    height: int = 360
    fps: int = 24
    remotion_version: str = "4.0.506"
    react_version: str = "19.0.0"
    typescript_version: str = "5.9.3"
    compiler_version: str = "1.0.0"
    seed: int = 0
    def __post_init__(self):
        from .qa_common import positive_int, token
        for name in ("width", "height", "fps"):
            positive_int(getattr(self, name), name)
        for name in ("remotion_version", "react_version", "typescript_version", "compiler_version"):
            token(getattr(self, name), name)
        if type(self.seed) is not int:
            raise CompilerQAError("target seed must be an integer")


def native_qa_capabilities() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    for kind in sorted(EMITTERS):
        registry.register(CompilerCapability("comp:" + kind, "1.0.0", (kind,), ("render",), ("web",), True))
    return registry

@dataclass(frozen=True)
class GeneratedSceneQABundle:
    scene_id: str
    scene_fingerprint: str
    codegen: CodegenPlan
    source_map: GeneratedSourceMap
    context: DeterminismContext
    capability_qa: CapabilityFallbackQAReceipt
    findings: tuple[QAFinding, ...]
    element_results: tuple
    animation_results: tuple
    source_contract_passed: bool
    scope: str = "SCENE_IR_TO_GENERATED_SOURCE_QA_ADAPTER"
    accepted: bool = False


def compile_scene_for_qa(payload, *, target: CompilerQATarget | None = None,
                         extra_dependency_versions: Mapping[str, str] | None = None) -> GeneratedSceneQABundle:
    target = target or CompilerQATarget()
    loaded = load_scene_ir_payload(payload)
    doc = loaded.document
    raw = doc.to_dict()
    canonical_json(raw)  # Reject NaN/Infinity before code generation.
    element_results, animation_results, findings, origins = [], [], [], {}
    files, layers = [], []
    duration = (doc.duration_ms * target.fps + 999) // 1000
    native = native_qa_capabilities()
    extra = dict(extra_dependency_versions or {})
    def origin_for_element(eid):
        index = next(i for i, e in enumerate(doc.elements) if e.element_id == eid)
        e = doc.elements[index]
        return SourceOrigin(doc.scene_id, f"$.elements[{index}]", eid, None, e.source_refs, e.reasoning_refs)
    for e in doc.elements:
        compiler = EMITTERS.get(e.element_type)
        if compiler is None:
            raise CompilerQAError("EMITTER_UNAVAILABLE:" + e.element_type)
        # Thawed JSON-compatible input avoids MappingProxyType serialization shortcuts.
        element = next(x for x in raw["elements"] if x["element_id"] == e.element_id)
        result = compiler(element)
        element_results.append(result)
        files.append(emitted_file(result.source_path, result.source_text))
        origins[result.source_path] = origin_for_element(e.element_id)
        for dep in result.required_dependencies:
            if dep not in extra:
                findings.append(QAFinding("DEPENDENCY_VERSION_NOT_GOVERNED", "ERROR",
                    "Required dependency has no explicit version: " + dep, result.source_path))
        tracks = [t for t in doc.tracks if t.element_id == e.element_id]
        wrappers = []
        for track in tracks:
            result_track = compile_animation_track(track)
            animation_results.append(result_track)
            files.append(emitted_file(result_track.source_path, result_track.source_text))
            idx = next(i for i, x in enumerate(doc.tracks) if x.track_id == track.track_id)
            origins[result_track.source_path] = SourceOrigin(doc.scene_id, f"$.tracks[{idx}]",
                        e.element_id, track.track_id, track.source_refs, track.reasoning_refs)
            wrapper_name = result_track.source_path.rsplit("/", 1)[-1][:-4]
            wrappers.append((wrapper_name, "../animations/" + wrapper_name))
            # The unchanged generic track emitter calculates data-bie-progress but applies no visual transform.
            if "data-bie-progress={progress}" in result_track.source_text and "style=" not in result_track.source_text:
                findings.append(QAFinding("ANIMATION_TRACK_NO_VISUAL_EFFECT", "ERROR",
                    "Track progress is emitted only as metadata, not a visible animation.", result_track.source_path))
            if (track.start_ms * target.fps + 500) // 1000 == (track.end_ms * target.fps + 500) // 1000:
                findings.append(QAFinding("ANIMATION_FRAME_RANGE_COLLAPSES", "ERROR",
                    "Track endpoints quantize to the same frame.", result_track.source_path))
        wrapper = component_name("QALayer", e.element_id)
        imports = ['import React from "react";',
                   f'import {{{result.component_name}}} from "../elements/{result.component_name}";']
        imports += [f'import {{{name}}} from {jsx(path)};' for name, path in wrappers]
        body = f'<{result.component_name} />'
        for name, _ in reversed(wrappers):
            body = f'<{name}>{body}</{name}>'
        box = element.get("normalized_box")
        if box is None:
            findings.append(QAFinding("LAYOUT_BINDING_NOT_PROVIDED", "ERROR",
                    "QA assembly requires an explicit normalized box; no layout is invented.", f"$.elements[{e.element_id}]"))
            style = {}
        else:
            style = {"position": "absolute", "left": str(box["x"] * 100) + "%",
                     "top": str(box["y"] * 100) + "%", "width": str(box["width"] * 100) + "%",
                     "height": str(box["height"] * 100) + "%"}
        content = "\n".join(imports) + f'\nexport const {wrapper}: React.FC = () => {{\n  return <div style={{{jsx(style)}}}>{body}</div>;\n}};\n'
        path = f"src/qa-layers/{wrapper}.tsx"
        files.append(emitted_file(path, content))
        origins[path] = origin_for_element(e.element_id)
        layers.append({"layer_id": e.element_id, "component_name": wrapper,
                       "import_path": "./qa-layers/" + wrapper, "from_frame": 0,
                       "duration_in_frames": duration, "props": {}})
    for field in ("events", "narration_cues", "interaction_cues", "interaction_bindings", "state_bindings", "simulation_controls"):
        if raw[field]:
            findings.append(QAFinding("UNCONSUMED_SCENE_CONTRACT", "ERROR",
                       "QA adapter does not silently consume or discard: " + field, "$." + field))
    files += list(emit_react_project(project_name="bie-qa-" + digest(doc.scene_id)[:12],
                remotion_version=target.remotion_version, react_version=target.react_version,
                typescript_version=target.typescript_version, extra_dependencies=extra))
    files += [emit_root(), emit_composition(composition_id="BieQA" + digest(doc.scene_id)[:16],
                    width=target.width, height=target.height, fps=target.fps, duration_in_frames=duration),
              emit_scene_component(layers=layers)]
    source_identity = {
        "scene_id": doc.scene_id, "scene_fingerprint": doc.fingerprint,
        "source_refs": list(doc.source_refs), "reasoning_refs": list(doc.reasoning_refs),
        "fixture_metadata": raw["metadata"], "target": asdict(target), "accepted": False,
    }
    files.append(emitted_file("src/bie-source-identity.json", canonical_json(source_identity).decode() + "\n"))
    codegen = plan_deterministic_codegen(scene_fingerprint=doc.fingerprint,
                  compiler_version=target.compiler_version, deterministic_seed=target.seed,
                  component_snapshot=native.snapshot(), files=[(f.path, f.content) for f in files])
    scene_origin = SourceOrigin(doc.scene_id, "$", None, None, doc.source_refs, doc.reasoning_refs)
    spans = [GeneratedSourceSpan(f.path, 1, max(1, len(f.content.splitlines())), f.sha256,
                 origins.get(f.path, scene_origin)) for f in codegen.files if f.path.endswith((".ts", ".tsx"))]
    source_map = build_source_map(scene_fingerprint=doc.fingerprint, files=codegen.files, spans=spans)
    package = next(f.content for f in codegen.files if f.path == "package.json")
    import json
    deps = json.loads(package)
    context = DeterminismContext(doc.fingerprint, target.compiler_version, target.seed,
                 digest({"dependencies": deps["dependencies"], "devDependencies": deps["devDependencies"],
                         "target": asdict(target), "lock_state": "PACKAGE_DECLARATIONS_NOT_INSTALLED_LOCK"}),
                 digest(native.snapshot()))
    capability = evaluate_capability_fallbacks(doc, native, element_results)
    findings.extend(capability.findings)
    ordered = ordered_findings(findings)
    return GeneratedSceneQABundle(doc.scene_id, doc.fingerprint, codegen, source_map, context,
                   capability, ordered, tuple(element_results), tuple(animation_results),
                   not any(f.severity == "ERROR" for f in ordered))
