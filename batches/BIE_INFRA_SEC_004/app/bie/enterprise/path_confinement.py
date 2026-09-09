
from pathlib import Path
class PathSecurityError(PermissionError): pass
def confined_path(root,candidate):
 root=Path(root).resolve(); p=(root/candidate).resolve()
 try:p.relative_to(root)
 except ValueError:raise PathSecurityError("path escape")
 return p
def assert_no_symlink_escape(root,candidate):
 p=confined_path(root,candidate); r=Path(root).resolve()
 cur=r
 for part in p.relative_to(r).parts:
  cur=cur/part
  if cur.exists() and cur.is_symlink() and not cur.resolve().is_relative_to(r): raise PathSecurityError("symlink escape")
 return p
