from hashing import sha256

def verify_artifact(manifest_record,artifact_content):
    actual=sha256(artifact_content)
    return {"artifact_id":manifest_record["artifact_id"],
            "expected_hash":manifest_record["artifact_hash"],
            "actual_hash":actual,
            "match":actual==manifest_record["artifact_hash"]}

def verify_manifest(m):
    return bool(m.get("artifact_id") and m.get("artifact_hash")
                and m.get("schema_version")=="5.90")
