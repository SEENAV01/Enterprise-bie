from __future__ import annotations
from ..canonical import fingerprint
from .contracts import *
def make_receipt(ctx:CompilerContext,artifacts):
    hashes=tuple(sorted((a.path,a.sha256) for a in artifacts));body={'input':fingerprint(ctx),'hashes':hashes,'profile':ctx.compile_profile};rid='compile:'+fingerprint(body)[7:31]
    return CompileReceipt(rid,fingerprint(ctx),fingerprint(body),hashes,ctx.compile_profile,True,True,False).validate()
