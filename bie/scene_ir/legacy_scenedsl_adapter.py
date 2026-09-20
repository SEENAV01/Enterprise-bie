from .migration_common import *

TYPE_MAP={
 "Text":"text","Equation":"equation","Shape":"shape","Vector":"vector","Diagram":"diagram",
 "Graph":"graph","Chart":"chart","Map":"map","Timeline":"timeline","Image":"image",
 "Video":"video","Simulation":"simulation","Model2D":"model2d","Model3D":"model3d",
 "Annotation":"annotation","Callout":"callout","Highlight":"highlight","Particles":"particle_system"
}

def adapt_legacy_scenedsl(doc):
    if not isinstance(doc,dict) or doc.get("format")!="legacy-scenedsl":
        raise DSLMigrationError("not legacy SceneDSL")
    scene_id=tok(doc.get("scene_id"),"scene_id")
    duration=doc.get("duration_ms",0)
    if isinstance(duration,bool) or not isinstance(duration,int) or duration<1:
        raise DSLMigrationError("duration_ms invalid")
    source_refs=tuple(doc.get("source_refs",()))
    reasoning_refs=tuple(doc.get("reasoning_refs",()))
    if not source_refs or not reasoning_refs:
        raise DSLMigrationError("legacy scene lineage missing")
    elements=[]
    for node in doc.get("nodes",()):
        lt=node.get("type")
        if lt not in TYPE_MAP:
            raise DSLMigrationError(f"unsupported legacy node type {lt}")
        elements.append({
          "element_id":tok(node.get("id"),"node.id"),
          "element_type":TYPE_MAP[lt],
          "source_refs":tuple(node.get("source_refs") or source_refs),
          "reasoning_refs":tuple(node.get("reasoning_refs") or reasoning_refs),
          "props":dict(node.get("props",{})),
          "accessibility":dict(node.get("accessibility",{})),
        })
    if not elements:
        raise DSLMigrationError("legacy SceneDSL contains no nodes")
    valid={e["element_id"] for e in elements}
    tracks=[]
    for anim in doc.get("animations",()):
        target=tok(anim.get("target"),"animation.target")
        if target not in valid:
            raise DSLMigrationError("animation target missing after migration")
        start=anim.get("start_ms",0);end=anim.get("end_ms",0)
        if not isinstance(start,int) or isinstance(start,bool) or not isinstance(end,int) or isinstance(end,bool) or start<0 or end<=start or end>duration:
            raise DSLMigrationError("legacy animation interval invalid")
        tracks.append({
          "track_id":tok(anim.get("id"),"animation.id"),
          "element_id":target,
          "action":tok(anim.get("action"),"animation.action"),
          "start_ms":start,"end_ms":end,
          "parameters":dict(anim.get("parameters",{})),
          "source_refs":tuple(anim.get("source_refs") or source_refs),
          "reasoning_refs":tuple(anim.get("reasoning_refs") or reasoning_refs),
        })
    out={
      "scene_id":scene_id,"schema_version":"1.0.0","title":doc.get("title") or scene_id,
      "duration_ms":duration,"elements":elements,"tracks":tracks,
      "source_refs":source_refs,"reasoning_refs":reasoning_refs,
      "compiler_capabilities":tuple(doc.get("compiler_capabilities",())),
      "metadata":{"migrated_from":"legacy-scenedsl","legacy_revision":doc.get("revision")},
      "review_required":True,"accepted":False,
    }
    out["ir_fingerprint"]=fp(out)
    evidence=MigrationEvidence(
      "legacy-scenedsl-adapter","legacy-scenedsl","scene-ir-1.0",
      fp(doc),out["ir_fingerprint"],True,True,False,(),False
    )
    return out,evidence
