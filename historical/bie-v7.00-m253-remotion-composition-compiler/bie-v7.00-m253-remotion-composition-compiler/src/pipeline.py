from compiler import compile_composition,validate_composition
from react_codegen import generate_react_source,validate_react_source
from assets import bind_assets
from render_job import build_render_job,validate_render_job
from metadata import build_metadata,validate_metadata

def build_m253_runtime():
    scene={"scene_id":"scene-c-field","fps":30,"duration_in_frames":120,
           "width":1920,"height":1080,"title":"Electric Field"}
    layers=[
      {"id":"bg","type":"background"},
      {"id":"diagram","type":"diagram","asset_id":"field-diagram"},
      {"id":"equation","type":"equation"}]
    registry={"field-diagram":{"path":"assets/field-diagram.svg","type":"svg"}}

    comp=compile_composition(scene)
    comp_check=validate_composition(comp)
    bindings=bind_assets(layers,registry)
    source=generate_react_source(comp,bindings["layers"])
    source_check=validate_react_source(source)
    job=build_render_job(comp)
    job_check=validate_render_job(job)
    meta=build_metadata(comp,scene)
    meta_check=validate_metadata(meta)
    valid=all([comp_check["valid"],bindings["valid"],source_check["valid"],
               job_check["valid"],meta_check["valid"]])
    return {"schema_version":"7.00","composition":comp,
            "composition_validation":comp_check,"asset_bindings":bindings,
            "react_source":source,"react_validation":source_check,
            "render_job":job,"render_validation":job_check,
            "metadata":meta,"metadata_validation":meta_check,
            "compiler_gate":{"valid":valid,"errors":[] if valid else ["COMPILER_GATE_FAILURE"]}}
