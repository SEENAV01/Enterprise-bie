class E(ValueError):pass
def evaluate(expected_pages,observed_pages,min_ratio=.98):
 if expected_pages<1 or not 0<=min_ratio<=1:raise E("input")
 valid={p for p in observed_pages if 1<=p<=expected_pages}
 ratio=len(valid)/expected_pages
 return {"ratio":ratio,"passed":ratio>=min_ratio,"missing":tuple(p for p in range(1,expected_pages+1) if p not in valid)}
