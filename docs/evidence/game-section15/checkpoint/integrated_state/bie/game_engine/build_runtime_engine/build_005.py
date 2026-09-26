from .exception_capture import capture_node_exception,capture_browser_exception
def execute(dist,policy=None):
 from .contracts import BuildPolicy
 p=policy or BuildPolicy();return (capture_node_exception(p),capture_browser_exception(dist,p))
