from .browser_runtime import browser_smoke
def execute(dist,policy=None):
 from .contracts import BuildPolicy
 return browser_smoke(dist,policy or BuildPolicy())
