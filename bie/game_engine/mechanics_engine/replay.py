from __future__ import annotations
from ..canonical import fingerprint
from .errors import MechanicError

def verify_replay(executor,*args,**kwargs):
    a=executor(*args,**kwargs);b=executor(*args,**kwargs)
    if fingerprint(a)!=fingerprint(b):raise MechanicError('GAME_MECH_REPLAY_NONDETERMINISTIC')
    return {'verified':True,'result_fingerprint':fingerprint(a),'product_accepted':False}
