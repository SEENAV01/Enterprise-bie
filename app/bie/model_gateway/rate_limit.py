
from dataclasses import dataclass
class RateLimitError(ValueError):pass
@dataclass
class Bucket:
 capacity:float;tokens:float;refill_per_second:float;updated_at:float
def consume(b,amount,now):
 if b.capacity<=0 or b.refill_per_second<0 or amount<=0:raise RateLimitError("invalid bucket/request")
 elapsed=max(0,now-b.updated_at);b.tokens=min(b.capacity,b.tokens+elapsed*b.refill_per_second);b.updated_at=now
 if b.tokens<amount:return False
 b.tokens-=amount;return True
