class TemplateRegistry:
    def __init__(self): self.templates={}
    def register(self,template_id,asset_type,parameters,defaults=None):
        self.templates[template_id]={"template_id":template_id,
          "asset_type":asset_type,"parameters":parameters,
          "defaults":defaults or {}}
    def instantiate(self,template_id,values=None):
        t=self.templates[template_id]
        params=t["defaults"].copy(); params.update(values or {})
        missing=[p for p in t["parameters"] if p not in params]
        if missing: raise ValueError("MISSING_TEMPLATE_PARAMETERS")
        return {"template_id":template_id,"asset_type":t["asset_type"],
                "parameters":params}
