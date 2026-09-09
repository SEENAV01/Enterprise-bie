from manifest import deliverable_manifest,artifact_record
from build import build_record
from licensing import validate_licenses
from accessibility import accessibility_metadata,accessibility_check
from package import package_index,package_quality_gate

def compile_delivery(course_id,title,version,artifacts,provenance,
                     assets,build_id,renderer_version,engine_version,
                     language="en"):
    manifest=deliverable_manifest(course_id,title,version,artifacts,
                                  captions=["captions.vtt"],
                                  accessibility=accessibility_metadata(language))
    build=build_record(build_id,renderer_version=renderer_version,
                       engine_version=engine_version)
    lic=validate_licenses(assets)
    acc=accessibility_check(manifest["accessibility"])
    package=package_index(manifest,provenance,build,lic)
    gate=package_quality_gate(manifest,provenance,build,lic)
    gate["errors"] += acc["errors"]
    gate["valid"] = gate["valid"] and acc["valid"]
    return {"schema_version":"5.17","package":package,
            "accessibility_check":acc,"quality_gate":gate}
