
class AdapterError(ValueError):pass
class GeminiAdapter:
 provider="google"
 def __init__(self,client,model):self.client=client;self.model=model
 def invoke(self,request):
  if not request.messages:raise AdapterError("messages")
  raw=self.client.generate(model=self.model,messages=request.messages,schema=request.response_schema)
  return {"provider":self.provider,"model":self.model,"content":raw["content"],"usage":raw.get("usage",{}),"finish_reason":raw.get("finish_reason","unknown")}
