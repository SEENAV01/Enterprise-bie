
from dataclasses import dataclass
class CredentialError(PermissionError): pass
@dataclass(frozen=True)
class CredentialGrant: subject:str; scopes:frozenset; expires_at:float
def authorize(grant,scope,now):
 if not grant.subject or now>=grant.expires_at: raise CredentialError("invalid/expired grant")
 if scope not in grant.scopes: raise CredentialError("scope denied")
 return True
