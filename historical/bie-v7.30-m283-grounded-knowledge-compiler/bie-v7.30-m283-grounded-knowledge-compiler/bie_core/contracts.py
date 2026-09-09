from typing import Protocol
from .models import RunContext

class Stage(Protocol):
    name: str
    def execute(self, ctx: RunContext) -> RunContext: ...

class Gate(Protocol):
    name: str
    def check(self, ctx: RunContext) -> bool: ...
