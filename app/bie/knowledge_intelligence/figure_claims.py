class E(ValueError):pass
def bind(fig,claim,visual_role,anchor):
 if not fig or not claim or visual_role not in {"ILLUSTRATES","EVIDENCES","CONTRASTS","LOCATES","PLOTS"} or not anchor:raise E("figure claim")
 return {"figure_id":fig,"claim_id":claim,"visual_role":visual_role,"anchor_id":anchor}
