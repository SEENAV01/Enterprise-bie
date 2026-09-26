from __future__ import annotations
from .contracts import *
from .errors import MechanicError

def validate_studio_mechanic(d:MechanicDefinition):
    d.validate()
    if d.kind!=MechanicKind.RETRIEVAL and not any(m.state_binding for m in d.motion):raise MechanicError('GAME_MECH_MOTION_STATE_BINDING_REQUIRED')
    if not all(a.accessible_label for a in d.actions):raise MechanicError('GAME_MECH_ACCESSIBLE_ACTION_REQUIRED')
    if any(a.action_kind in {ActionKind.DRAG,ActionKind.DROP,ActionKind.ADJUST,ActionKind.PLACE,ActionKind.ORDER} and not a.keyboard_equivalent for a in d.actions):raise MechanicError('GAME_MECH_KEYBOARD_EQUIVALENT_REQUIRED')
    if d.quality.answer_reveal_before_attempt or d.quality.speed_pressure_required:raise MechanicError('GAME_MECH_STUDIO_POLICY')
    return d
