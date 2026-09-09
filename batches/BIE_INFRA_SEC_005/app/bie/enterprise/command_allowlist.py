
import shlex
class CommandSecurityError(PermissionError): pass
class CommandPolicy:
 def __init__(self,allowed):self.allowed=set(allowed)
 def validate(self,argv):
  if isinstance(argv,str): raise CommandSecurityError("shell strings forbidden")
  if not argv or argv[0] not in self.allowed: raise CommandSecurityError("command denied")
  bad={";","&&","||","`","$(",">","<"}
  if any(any(b in str(a) for b in bad) for a in argv): raise CommandSecurityError("shell metacharacter denied")
  return tuple(argv)
