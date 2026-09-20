from .migration_common import *

PANE_ROLES={"title":"heading","left":"content","center":"content","right":"content","footer":"caption"}

def adapt_five_pane(doc):
    if not isinstance(doc,dict) or doc.get("format")!="five-pane":
        raise DSLMigrationError("not five-pane format")
    source_refs=tuple(doc.get("source_refs",()))
    reasoning_refs=tuple(doc.get("reasoning_refs",()))
    if not source_refs or not reasoning_refs:
        raise DSLMigrationError("five-pane lineage missing")
    scene_id=tok(doc.get("scene_id"),"scene_id")
    panes=dict(doc.get("panes",{}))
    unknown=set(panes)-set(PANE_ROLES)
    if unknown:
        raise DSLMigrationError("unknown pane(s): "+",".join(sorted(unknown)))
    boxes={
      "title":(0.05,0.02,0.90,0.12),
      "left":(0.02,0.18,0.30,0.65),
      "center":(0.34,0.18,0.32,0.65),
      "right":(0.67,0.18,0.31,0.65),
      "footer":(0.05,0.88,0.90,0.08),
    }
    elements=[]
    for name in ("title","left","center","right","footer"):
        pane=panes.get(name)
        if not pane or pane.get("content") is None:
            continue
        x,y,width,height=boxes[name]
        elements.append({
          "element_id":"pane:"+name,
          "element_type":"text" if pane.get("kind","text")=="text" else tok(pane.get("kind"),"pane.kind"),
          "source_refs":tuple(pane.get("source_refs") or source_refs),
          "reasoning_refs":tuple(pane.get("reasoning_refs") or reasoning_refs),
          "props":{"text":str(pane["content"]),"legacy_pane":name,"role":PANE_ROLES[name]},
          "accessibility":{"reading_order":len(elements)},
          "normalized_box":{"x":x,"y":y,"width":width,"height":height},
        })
    if not elements:
        raise DSLMigrationError("five-pane contains no content")
    duration=doc.get("duration_ms",1000)
    if isinstance(duration,bool) or not isinstance(duration,int) or duration<1:
        raise DSLMigrationError("duration invalid")
    out={
      "scene_id":scene_id,"schema_version":"1.0.0","title":doc.get("title") or scene_id,
      "duration_ms":duration,"elements":elements,"tracks":[],
      "source_refs":source_refs,"reasoning_refs":reasoning_refs,
      "compiler_capabilities":(),
      "metadata":{"migrated_from":"five-pane","pane_count":len(elements)},
      "review_required":True,"accepted":False,
    }
    out["ir_fingerprint"]=fp(out)
    evidence=MigrationEvidence(
      "five-pane-adapter","five-pane","scene-ir-1.0",
      fp(doc),out["ir_fingerprint"],True,True,False,(),False
    )
    return out,evidence
