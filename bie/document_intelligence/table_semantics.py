
class TableSemanticError(ValueError):pass
def infer(headers,rows):
 if not headers:raise TableSemanticError("headers required")
 if len(set(headers))!=len(headers):raise TableSemanticError("duplicate headers")
 width=len(headers)
 if any(len(r)!=width for r in rows):raise TableSemanticError("ragged table")
 cols={h:tuple(r[i] for r in rows) for i,h in enumerate(headers)}
 return {"headers":tuple(headers),"columns":cols,"row_count":len(rows)}
