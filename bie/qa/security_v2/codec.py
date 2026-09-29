"""Narrow optional-receipt adapter; inherited codecs/contracts remain unchanged."""
from ..release_v2.contracts import ArtifactRef,ContractError
from ..repair_v2.codec import decode as inherited_decode
from ..repair_v2.models import Snapshot
from .models import SecurityRequest

def decode(value,cls):
    if cls is not SecurityRequest:return inherited_decode(value,cls)
    if type(value) is not dict or set(value)!={'snapshot','sandbox_evidence'}:raise ContractError('SEC_REQUEST_FIELDS')
    receipt=value['sandbox_evidence']
    return SecurityRequest(inherited_decode(value['snapshot'],Snapshot),None if receipt is None else inherited_decode(receipt,ArtifactRef))
