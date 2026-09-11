"""RE-TEMP-025 — Normalize calendar/era labels without silently converting unknown systems."""
from dataclasses import dataclass

@dataclass(frozen=True)
class CalendarDate:
    year:int
    era:str="CE"

def normalize_year(d:CalendarDate)->int:
    era=d.era.strip().upper()
    if era in {"CE","AD"}: return d.year
    if era in {"BCE","BC"}:
        if d.year <= 0: raise ValueError("BCE/BC year must be positive")
        return 1-d.year  # astronomical year numbering
    raise ValueError("unsupported calendar/era")

def compare_dates(a:CalendarDate,b:CalendarDate)->str:
    x,y=normalize_year(a),normalize_year(b)
    return "BEFORE" if x<y else "AFTER" if x>y else "SAME_YEAR"
