def package_index(manifest,provenance,build_record,licenses):
    return {"manifest":manifest,"provenance":provenance,
            "build":build_record,"licenses":licenses,
            "package_format":"BIE-PACKAGE-1"}

def package_quality_gate(manifest,provenance,build_record,licenses):
    errors=[]
    if manifest.get("status")!="READY": errors.append("MANIFEST_NOT_READY")
    if not build_record.get("build_fingerprint"): errors.append("BUILD_FINGERPRINT_MISSING")
    if not licenses.get("valid",False): errors += licenses.get("errors",[])
    if not provenance: errors.append("PROVENANCE_EMPTY")
    return {"valid":not errors,"errors":errors}
