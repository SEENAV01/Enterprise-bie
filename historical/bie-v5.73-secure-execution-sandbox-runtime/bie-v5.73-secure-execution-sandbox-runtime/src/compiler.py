from sandbox import sandbox_gate
from output import output_allowed
from termination import timed_out

def validate_runtime(spec,artifact=None,duration_seconds=None):
    gate=sandbox_gate(spec)
    errors=list(gate["missing"])
    if artifact is not None and not output_allowed(artifact,spec["limits"]):
        errors.append("OUTPUT_LIMIT")
    if duration_seconds is not None and timed_out(duration_seconds,spec["limits"]):
        errors.append("TIMEOUT")
    return {"schema_version":"5.73",
            "valid":not errors,"errors":errors}
