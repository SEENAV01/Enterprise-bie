"""Closed dataclass wire decoding; no dynamic imports or executable fields."""
from ..repair_v2.codec import decode
from ..source_v2.codec import loads
from .models import AuditRequest,AuditPolicy

def load_request(data):return decode(loads(data),AuditRequest)
def load_policy(data):return decode(loads(data),AuditPolicy)
