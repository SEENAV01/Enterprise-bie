
from dataclasses import dataclass
class RetryError(ValueError):pass
@dataclass(frozen=True)
class RetryPolicy:max_attempts:int;base_delay:float;max_delay:float
RETRYABLE={"timeout","rate_limit","provider_unavailable","server_error"}
def validate(p):
 if p.max_attempts<1 or p.base_delay<0 or p.max_delay<p.base_delay:raise RetryError("invalid policy")
 return True
def should_retry(kind,attempt,p):
 validate(p);return kind in RETRYABLE and attempt<p.max_attempts
def delay(attempt,p):
 validate(p);return min(p.max_delay,p.base_delay*(2**max(0,attempt-1)))
