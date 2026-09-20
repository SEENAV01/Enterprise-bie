"""H5 explicit content-replacement dispatch. Generic motions retain their existing path."""
from .specialized_motion import specialized_contract, validate_binding, fail


def compile_specialized_track(track, element, *, typesetter=None):
    from .specialized_camera import compile_specialized_camera
    from .specialized_equation import compile_specialized_equation
    from .specialized_trace import compile_specialized_trace
    if element is None: fail('SPECIALIZED_TARGET_REQUIRED', 'source element must accompany a specialized track')
    c = specialized_contract(track)
    if element['element_id'] != c.element_id: fail('SPECIALIZED_TARGET_MISMATCH', 'wrong source element')
    return {'camera':compile_specialized_camera, 'morph':compile_specialized_equation,
            'trace':compile_specialized_trace}[c.action](track, element, typesetter=typesetter)
