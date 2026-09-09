
class AdapterError(ValueError):pass
class GPTAdapter:
 provider="openai"
 def __init__(self,client,model):self.client=client;self.model=model
 def invoke(self,request):
  if not request.messages:raise AdapterError("messages")
  raw=self.client.responses_create(model=self.model,messages=request.messages,response_schema=request.response_schema)
  return {"provider":self.provider,"model":self.model,"content":raw["content"],"usage":raw.get("usage",{}),"finish_reason":raw.get("finish_reason","unknown")}
