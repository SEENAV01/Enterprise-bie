
class FallbackError(RuntimeError):pass
def execute(candidates,invoke,is_retryable):
 errors=[]
 for c in candidates:
  try:return c,invoke(c)
  except Exception as e:
   errors.append((c,type(e).__name__))
   if not is_retryable(e):raise
 raise FallbackError("all candidates failed: "+str(errors))
