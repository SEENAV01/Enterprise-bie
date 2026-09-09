def replay_plan(manifest_record):
    return {
      "artifact_id":manifest_record["artifact_id"],
      "inputs":manifest_record.get("inputs",[]),
      "model":manifest_record.get("model"),
      "prompt":manifest_record.get("prompt"),
      "config":manifest_record.get("config"),
      "code":manifest_record.get("code"),
      "dependencies":manifest_record.get("dependencies",[]),
      "environment":manifest_record.get("environment",{})
    }

def replay_ready(plan):
    required=["model","prompt","config","code"]
    return all(plan.get(k) is not None for k in required)
