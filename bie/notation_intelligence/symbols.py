from dataclasses import dataclass
@dataclass(frozen=True)
class SymbolMeaning:
 symbol:str; meaning:str; scope:str
@dataclass(frozen=True)
class SymbolResolution:
 symbol:str; meanings:tuple[str,...]; ambiguous:bool
def resolve_symbols(definitions:list[SymbolMeaning],scope:str)->list[SymbolResolution]:
 grouped={}
 for d in definitions:
  if d.scope in {scope,"global"}: grouped.setdefault(d.symbol,set()).add(d.meaning)
 return [SymbolResolution(s,tuple(sorted(ms)),len(ms)>1) for s,ms in sorted(grouped.items())]
