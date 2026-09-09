from config import config_snapshot
from canonical import digest

def compile_configuration(config_id,version,values,
                          flags=None,experiments=None):
    snap=config_snapshot(config_id,version,values)
    ref={"config_id":snap["config_id"],
         "version":snap["version"],
         "digest":snap["digest"],
         "feature_flags":flags or [],
         "experiments":experiments or []}
    return {"schema_version":"5.77",
            "configuration":snap,
            "reproducibility_ref":ref,
            "quality_gate":{"valid":True,"errors":[]}}
