
class LocalAdapterError(ValueError):pass
class LocalModelAdapter:
 provider="local"
 def __init__(self,runtime,model):self.runtime=runtime;self.model=model
 def invoke(self,request):
  if not request.messages:raise LocalAdapterError("messages")
  raw=self.runtime.generate(self.model,request.messages,request.response_schema)
  return {"provider":"local","model":self.model,"content":raw["content"],"usage":raw.get("usage",{}),"finish_reason":raw.get("finish_reason","stop")}
