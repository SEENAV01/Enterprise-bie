"""Data-only strict decoding; command producers never come from audit request JSON."""
from ..repair_v2.codec import decode
from ..source_v2.codec import loads
__all__=['decode','loads']
