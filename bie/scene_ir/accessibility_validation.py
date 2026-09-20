from .validation_common import *

def validate_accessibility(doc):
    issues=[]
    for i,e in enumerate(doc.get("elements",())):
        et=e.get("element_type")
        acc=e.get("accessibility",{}) or {}
        if et in {"image","diagram","graph","chart","map","model2d","model3d"} and not (acc.get("alt") or acc.get("long_description_ref")):
            issues.append(issue("VISUAL_DESCRIPTION_MISSING",f"$.elements[{i}].accessibility","Visual alternative required"))
        if et=="video" and not (acc.get("captions_ref") or acc.get("transcript_ref")):
            issues.append(issue("VIDEO_TEXT_ALTERNATIVE_MISSING",f"$.elements[{i}].accessibility","Captions or transcript required"))
        if et in {"simulation","particle_system"} and not acc.get("reduced_motion_variant"):
            issues.append(issue("REDUCED_MOTION_MISSING",f"$.elements[{i}].accessibility","Reduced-motion variant required"))
        if et in {"graph","chart","map"} and acc.get("color_independent_encoding") is not True:
            issues.append(issue("COLOR_ONLY_ENCODING",f"$.elements[{i}].accessibility","Color-independent encoding required"))
    return report("DSL-VALID-ACCESSIBILITY",issues)
