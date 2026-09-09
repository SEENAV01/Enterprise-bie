
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Tuple
class ConfigError(ValueError): pass

@dataclass(frozen=True)
class RunConfig:
    schema_version:int
    run_id:str
    source_ref:str
    enabled_outputs:Tuple[str,...]=("video","game")
    model_policy:str="quality_first"
    locale:str="en"
    deterministic:bool=True
    metadata:Tuple[Tuple[str,str],...]=()

    def validate(self):
        if self.schema_version < 1: raise ConfigError("invalid schema version")
        if not self.run_id.strip(): raise ConfigError("run_id required")
        if not self.source_ref.strip(): raise ConfigError("source_ref required")
        valid={"video","game"}
        if not self.enabled_outputs or not set(self.enabled_outputs).issubset(valid): raise ConfigError("invalid enabled outputs")
        if self.model_policy not in {"quality_first","balanced","offline_only"}: raise ConfigError("invalid model policy")
        if not self.locale.strip(): raise ConfigError("locale required")
        return self

    def to_canonical_dict(self):
        self.validate()
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "source_ref": self.source_ref,
            "enabled_outputs": sorted(self.enabled_outputs),
            "model_policy": self.model_policy,
            "locale": self.locale,
            "deterministic": self.deterministic,
            "metadata": {k:v for k,v in sorted(self.metadata)},
        }
