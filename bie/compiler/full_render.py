"""BIE-COMP-BUILD-008: whole-composition render, not a sample masquerading as full."""
from .render_contracts import RenderRequest, RenderReceipt, make_render_plan
from .render_runtime import execute_render

def full_render(request: RenderRequest, *, cancel_event=None, secrets=(), runner=None) -> RenderReceipt:
    return execute_render(request, make_render_plan(request, "full"),
                          cancel_event=cancel_event, secrets=secrets, runner=runner)
