from dataclasses import dataclass
@dataclass(frozen=True)
class SymbolMetadata:
 symbol:str; role:str; domain:str|None; unit:str|None; source:str|None
def make_metadata(symbol:str,role="variable",domain=None,unit=None,source=None)->SymbolMetadata:
 if not symbol or any(c.isspace() for c in symbol):raise ValueError("invalid symbol")
 if role not in {"variable","constant","parameter","function","index","operator"}:raise ValueError("invalid role")
 return SymbolMetadata(symbol,role,domain,unit,source)
