from dataclasses import dataclass
@dataclass(frozen=True)
class Matrix:
 rows:tuple[tuple[str,...],...]; nrows:int; ncols:int
def parse_matrix(s:str):
 s=(s or "").strip()
 if s.startswith("[") and s.endswith("]"):s=s[1:-1]
 rows=[r.strip() for r in s.split(";") if r.strip()]
 if not rows:return None
 parsed=[]
 for r in rows:
  cells=tuple(x.strip() for x in r.split(",") if x.strip())
  if not cells:return None
  parsed.append(cells)
 n=len(parsed[0])
 if any(len(r)!=n for r in parsed):raise ValueError("ragged matrix")
 return Matrix(tuple(parsed),len(parsed),n)
