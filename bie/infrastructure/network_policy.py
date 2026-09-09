
from urllib.parse import urlparse
import ipaddress
class NetworkSecurityError(PermissionError): pass
class NetworkPolicy:
 def __init__(self,allowed_hosts=()):self.allowed=set(h.lower() for h in allowed_hosts)
 def authorize(self,url):
  u=urlparse(url)
  if u.scheme!="https" or not u.hostname: raise NetworkSecurityError("https required")
  host=u.hostname.lower()
  try:
   ip=ipaddress.ip_address(host)
   if ip.is_private or ip.is_loopback or ip.is_link_local: raise NetworkSecurityError("private address denied")
  except ValueError:pass
  if host not in self.allowed: raise NetworkSecurityError("host denied")
  return True
