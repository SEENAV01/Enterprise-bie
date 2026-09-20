"""BIE-COMP-BUILD-007: a requested, bounded frame window; never a full-render claim."""
from .render_contracts import RenderRequest, RenderReceipt, make_render_plan
from .render_runtime import execute_render

def smoke_render(request: RenderRequest, *, first_frame: int = 0, frame_count: int = 12,
                 cancel_event=None, secrets=(), runner=None) -> RenderReceipt:
    plan = make_render_plan(request, "smoke", first_frame=first_frame, frame_count=frame_count)
    return execute_render(request, plan, cancel_event=cancel_event, secrets=secrets, runner=runner)
