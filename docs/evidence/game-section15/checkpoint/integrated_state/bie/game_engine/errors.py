from __future__ import annotations

class GameContractError(ValueError):
    """Stable fail-closed Section 15 GAME contract error."""
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(code + ((": " + detail) if detail else ""))
