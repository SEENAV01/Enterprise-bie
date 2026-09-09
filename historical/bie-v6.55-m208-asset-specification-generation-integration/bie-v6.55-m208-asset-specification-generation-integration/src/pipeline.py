from asset import asset, valid as asset_valid
from spec import specification, valid as spec_valid
from prompt import prompt, valid as prompt_valid
from diagram import diagram_spec, valid as diagram_valid
from equation import equation_spec, valid as equation_valid
from animation import animation_spec, valid as animation_valid
from asset_evidence import evidence_binding, grounded
from manifest import manifest, valid as manifest_valid
from provenance import provenance, traceable
from verification import verification, passed

def build_asset_generation_integration():
    a1 = asset(
        "asset-force-diagram", "DIAGRAM", "Explain electric force",
        "sc3", "Diagram showing attraction and repulsion.",
        {"canvas":"1920x1080","readable_labels":True},
        ["ev-force"]
    )
    a2 = asset(
        "asset-force-equation", "EQUATION", "State force relationship",
        "sc2", "Typeset equation for the lesson.",
        {"math_format":"LaTeX"},
        ["ev-force"]
    )
    a3 = asset(
        "asset-force-animation", "ANIMATION", "Animate force direction",
        "sc3", "Arrow motion illustrating force direction.",
        {"duration_sec":8},
        ["ev-force"]
    )

    s1 = specification(
        "spec-1", a1["asset_id"], "VECTOR_DIAGRAM",
        "1920x1080", "SVG", "clean educational",
        {"no_decorative_clutter":True}
    )
    s2 = specification(
        "spec-2", a2["asset_id"], "LATEX_RENDER",
        "1920x1080", "SVG", "typeset",
        {"high_contrast":True}
    )
    s3 = specification(
        "spec-3", a3["asset_id"], "CODE_ANIMATION",
        "1920x1080", "MP4", "instructional",
        {"fps":30}
    )

    p1 = prompt(
        "prompt-1", a1["asset_id"],
        "Create a clean educational diagram of two charged objects "
        "showing attraction and repulsion with clearly labeled force arrows.",
        "photorealistic clutter, unreadable labels",
        {"evidence_ids":["ev-force"]}
    )
    p2 = prompt(
        "prompt-2", a2["asset_id"],
        "Render the specified electric-force equation as clean educational typography.",
        None, {"evidence_ids":["ev-force"]}
    )
    p3 = prompt(
        "prompt-3", a3["asset_id"],
        "Animate force-direction arrows progressively and keep labels stable.",
        "camera shake, decorative motion",
        {"evidence_ids":["ev-force"]}
    )

    d = diagram_spec(
        a1["asset_id"], "FORCE_RELATIONSHIP",
        ["positive_charge","negative_charge"],
        [{"from":"positive_charge","to":"negative_charge","label":"attraction"}],
        ["positive charge","negative charge","force"]
    )
    eq = equation_spec(
        a2["asset_id"], "F = k q_1 q_2 / r^2",
        "electrostatic force magnitude", ["F","k","q_1","q_2","r"]
    )
    anim = animation_spec(
        a3["asset_id"], 8,
        [{"action":"DRAW_ARROW","target":"force"},
         {"action":"HOLD_LABELS","target":"all"}],
        "ease-in-out", {"type":"STATIC"}
    )

    bindings = [
        evidence_binding(a1["asset_id"], ["ev-force"], ["record-figure-1"], ["verify-1"]),
        evidence_binding(a2["asset_id"], ["ev-force"], ["record-text-1"], ["verify-1"]),
        evidence_binding(a3["asset_id"], ["ev-force"], ["record-figure-1"], ["verify-1"])
    ]

    m = manifest(
        "manifest-1", "storyboard-1",
        [a1, a2, a3],
        {"canvas":"1920x1080","fps":30,"language":"en"}
    )
    prov = provenance(
        m["manifest_id"], ["storyboard-1"],
        ["sc2","sc3"], ["ev-force"],
        ["artifact://lesson-script"]
    )
    check = verification(
        "verify-assets", m["manifest_id"], "PASS", ["ev-force"]
    )

    return {
        "schema_version":"6.55",
        "manifest":m,
        "specifications":[s1,s2,s3],
        "prompts":[p1,p2,p3],
        "diagram":d,
        "equation":eq,
        "animation":anim,
        "evidence_bindings":bindings,
        "provenance":prov,
        "verification":check,
        "quality_gate":{"valid":(
            manifest_valid(m)
            and all(asset_valid(a) for a in [a1,a2,a3])
            and all(spec_valid(s) for s in [s1,s2,s3])
            and all(prompt_valid(p) for p in [p1,p2,p3])
            and diagram_valid(d) and equation_valid(eq)
            and animation_valid(anim)
            and all(grounded(b) for b in bindings)
            and traceable(prov) and passed(check)
        ),"errors":[]}
    }
