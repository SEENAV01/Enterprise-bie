
class BrowserWorkerError(ValueError):pass
def validate_manifest(m):
 req={"node","chromium","playwright"}
 if not req.issubset(set(m.get("tools",[]))):raise BrowserWorkerError("browser/game toolchain incomplete")
 if m.get("network_default")!="deny":raise BrowserWorkerError("network must default deny")
 if not m.get("sandbox"):raise BrowserWorkerError("browser sandbox required")
 return True
