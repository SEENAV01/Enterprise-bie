"""H2-001: bounded real Mathtext SVG typesetting and inert MathML trees.

No TeX subprocess, remote assets, runtime HTML injection, or raw-text fallback.
The pinned backend is a deliberate adapter, not a claim of universal LaTeX support.
"""
from __future__ import annotations
from functools import lru_cache
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import re
import threading
import warnings
import xml.etree.ElementTree as ET
from .hardening_contracts import reject, text_value

MATPLOTLIB_VERSION = "3.10.8"
ADAPTER_VERSION = "bie.mathtext-svg.v1"
_LOCK = threading.RLock()
_MATH_TAGS = {"math", "mrow", "mi", "mn", "mo", "mtext", "mfrac", "msqrt", "mroot", "msub", "msup", "msubsup", "munder", "mover", "munderover", "mtable", "mtr", "mtd"}
_ARITY = {"mfrac": 2, "mroot": 2, "msub": 2, "msup": 2, "msubsup": 3, "munder": 2, "mover": 2, "munderover": 3}
_MATH_NS = "http://www.w3.org/1998/Math/MathML"
_SVG_NS = "http://www.w3.org/2000/svg"


def _tag(tag):
    return tag.rsplit("}", 1)[-1]


def mathml_tree(expression: str):
    text_value(expression, "MathML expression", maximum=12000)
    if re.search(r"<!|<\?", expression):
        reject("EQUATION_MATHML_UNSAFE", "DOCTYPE, entities, comments and processing instructions are forbidden")
    try:
        root = ET.fromstring(expression)
    except ET.ParseError as exc:
        reject("EQUATION_MATHML_INVALID", str(exc))
    if _tag(root.tag) != "math":
        reject("EQUATION_MATHML_INVALID", "root must be math")
    count = [0]
    def walk(node, depth=0):
        count[0] += 1
        if depth > 24 or count[0] > 512:
            reject("EQUATION_COMPLEXITY_LIMIT", "MathML exceeds 512 nodes / 24 levels")
        tag = _tag(node.tag)
        if (node.tag.startswith("{") and not node.tag.startswith("{" + _MATH_NS + "}")) or tag not in _MATH_TAGS:
            reject("EQUATION_MATHML_UNSAFE", "unsupported MathML tag")
        attrs = {}
        for key, val in node.attrib.items():
            allowed = {"display": {"inline", "block"}} if tag == "math" else {}
            if tag in {"mi", "mn", "mo", "mtext"}:
                allowed["mathvariant"] = {"normal", "bold", "italic", "bold-italic", "double-struck", "script", "fraktur", "monospace"}
            if key not in allowed or val not in allowed[key]:
                reject("EQUATION_MATHML_UNSAFE", "unsupported MathML attribute/value: " + key)
            attrs[key] = val
        children = list(node)
        if tag in _ARITY and len(children) != _ARITY[tag]:
            reject("EQUATION_MATHML_ARITY", tag + " has wrong child count")
        if tag in {"mi", "mn", "mo", "mtext"}:
            if children or not node.text or not node.text.strip():
                reject("EQUATION_MATHML_ARITY", "token must have nonempty text and no child elements")
        elif (node.text or "").strip() or any((c.tail or "").strip() for c in children):
            reject("EQUATION_MATHML_INVALID", "text must occur inside explicit MathML token elements")
        elif not children:
            reject("EQUATION_MATHML_ARITY", "empty MathML container")
        if tag == "mtable" and any(_tag(c.tag) != "mtr" for c in children):
            reject("EQUATION_MATHML_ARITY", "mtable needs mtr children")
        if tag == "mtr" and any(_tag(c.tag) != "mtd" for c in children):
            reject("EQUATION_MATHML_ARITY", "mtr needs mtd children")
        result_children = [node.text] if tag in {"mi", "mn", "mo", "mtext"} else [walk(c, depth + 1) for c in children]
        return {"tag": tag, "attrs": attrs, "children": result_children}
    tree = walk(root)
    tree["attrs"].setdefault("display", "block")
    return {"tree": tree, "renderer": "native-mathml-core.v1", "input_sha256": sha256(expression.encode()).hexdigest(), "accepted": False}


def _svg_tree(svg_bytes: bytes, prefix: str):
    """Convert trusted backend SVG to a small inert SVG vocabulary, fail closed."""
    root = ET.fromstring(svg_bytes)
    allowed = {"svg", "g", "defs", "path", "use", "rect"}
    names = {"stroke-width": "strokeWidth", "stroke-linejoin": "strokeLinejoin", "stroke-linecap": "strokeLinecap", "fill-rule": "fillRule", "clip-rule": "clipRule"}
    attrs_allowed = {"width", "height", "viewBox", "version", "d", "id", "transform", "x", "y", "fill", "stroke", "stroke-width", "stroke-linejoin", "stroke-linecap"}
    ids = {n.attrib["id"] for n in root.iter() if "id" in n.attrib}
    def walk(n):
        tag = _tag(n.tag)
        if tag == "metadata":
            return None  # Includes clock/creator metadata, never part of geometry identity.
        if tag == "style":
            if (n.text or "").strip() != "*{stroke-linejoin: round; stroke-linecap: butt}":
                reject("EQUATION_SVG_UNSAFE", "unexpected backend style")
            return None  # Baked as inherited SVG root properties below.
        if tag not in allowed:
            reject("EQUATION_SVG_UNSAFE", "unsupported backend SVG tag: " + tag)
        attrs = {}
        for key, value in n.attrib.items():
            key = _tag(key)
            if key == "style":
                style = {}
                for rule in value.split(";"):
                    if not rule.strip():
                        continue
                    k, v = [p.strip() for p in rule.split(":", 1)]
                    if k not in {"fill", "stroke", "stroke-width", "stroke-linejoin", "stroke-linecap"} or re.search(r"url|expression|[<>]", v, re.I):
                        reject("EQUATION_SVG_UNSAFE", "unexpected SVG style")
                    style[names.get(k, k)] = v
                attrs["style"] = style
            elif key == "href":
                if not value.startswith("#") or value[1:] not in ids:
                    reject("EQUATION_SVG_UNSAFE", "SVG reference must be a defined local glyph")
                attrs["href"] = "#" + prefix + value[1:]
            elif key in attrs_allowed:
                attrs[names.get(key, key)] = prefix + value if key == "id" else value
            else:
                reject("EQUATION_SVG_UNSAFE", "unexpected backend SVG attribute")
        children = [v for c in n for v in [walk(c)] if v is not None]
        return {"tag": tag, "attrs": attrs, "children": children}
    tree = walk(root)
    view = [float(v) for v in tree["attrs"]["viewBox"].split()]
    if len(view) != 4 or view[2] <= 0 or view[3] <= 0 or view[2] / view[3] > 60:
        reject("EQUATION_LAYOUT_UNSUPPORTED", "empty or excessively wide typeset layout")
    # The backend's tight canvas may clip descenders/radical strokes at a
    # fractional pixel boundary. Keep explicit proportional ink safety space.
    padding = max(1.0, view[3] * 0.04)
    view = [view[0] - padding, view[1] - padding, view[2] + 2*padding, view[3] + 2*padding]
    tree["attrs"]["viewBox"] = " ".join(format(v, ".12g") for v in view)
    tree["attrs"].update({"width": "100%", "height": "100%", "preserveAspectRatio": "xMidYMid meet", "strokeLinejoin": "round", "strokeLinecap": "butt"})
    return tree, view


@lru_cache(maxsize=128)
def _latex_cached(expression: str, element_id: str, font_size: int):
    # The cache stores immutable canonical JSON, not mutable shared dictionaries.
    try:
        import matplotlib as mpl
        from matplotlib import ft2font
        from matplotlib.font_manager import FontProperties
        from matplotlib.mathtext import MathTextParser, math_to_image
    except ImportError:
        reject("EQUATION_TYPESETTER_UNAVAILABLE", "install governed compiler-typesetting requirements")
    if mpl.__version__ != MATPLOTLIB_VERSION:
        reject("EQUATION_TYPESETTER_VERSION_MISMATCH", "expected matplotlib " + MATPLOTLIB_VERSION)
    wrapped = "$" + expression + "$"
    with _LOCK, mpl.rc_context(), warnings.catch_warnings():
        mpl.rcdefaults()
        mpl.rcParams.update({"text.usetex": False, "svg.fonttype": "path", "svg.hashsalt": "bie-h2-equation", "mathtext.fontset": "dejavusans", "savefig.transparent": True})
        warnings.simplefilter("error")
        try:
            prop = FontProperties(family="DejaVu Sans", size=font_size)
            parsed = MathTextParser("path").parse(wrapped, dpi=72, prop=prop)
            if len(parsed.glyphs) > 512:
                reject("EQUATION_COMPLEXITY_LIMIT", "too many glyphs")
            b = BytesIO()
            math_to_image(wrapped, b, prop=prop, dpi=72, format="svg", color="black")
            used_fonts = sorted({str(g[0].fname) for g in parsed.glyphs})
        except (ValueError, RuntimeError, Warning) as exc:
            reject("EQUATION_LATEX_UNSUPPORTED", str(exc))
    if len(b.getvalue()) > 1500000:
        reject("EQUATION_COMPLEXITY_LIMIT", "typeset geometry exceeds byte budget")
    prefix = "eq" + sha256((element_id + "\0" + expression).encode()).hexdigest()[:20] + "_"
    tree, view = _svg_tree(b.getvalue(), prefix)
    body = {"tree": tree, "view_box": view, "renderer": ADAPTER_VERSION,
            "input_sha256": sha256(expression.encode()).hexdigest(), "matplotlib_version": mpl.__version__,
            "freetype_version": ft2font.__freetype_version__,
            "font_hashes": {Path(p).name: sha256(Path(p).read_bytes()).hexdigest() for p in used_fonts},
            "dialect": "matplotlib-mathtext-subset-not-full-latex", "accepted": False}
    # Font hashes record identity; font files are neither copied nor redistributed.
    return json.dumps(body, sort_keys=True, ensure_ascii=True, allow_nan=False)


def typeset_latex(expression: str, *, element_id: str, font_size: int = 32):
    text_value(expression, "LaTeX expression", maximum=2048)
    text_value(element_id, "element_id", maximum=512)
    if type(font_size) is not int or not 12 <= font_size <= 96:
        reject("EQUATION_FONT_SIZE_INVALID", "font_size must be an integer in 12..96")
    if "$" in expression or "\n" in expression or "\r" in expression:
        reject("EQUATION_LATEX_UNSUPPORTED", "use one undelimited math expression")
    if re.search(r"\\(?:input|include|includegraphics|href|url|def|gdef|newcommand|write|html|class|style)\b", expression):
        reject("EQUATION_LATEX_UNSAFE", "external resources/macros/style commands are unsupported")
    depth = 0
    for ch in expression:
        if ch == "{": depth += 1
        if ch == "}": depth -= 1
        if depth > 24 or depth < 0:
            reject("EQUATION_COMPLEXITY_LIMIT", "invalid/excessive grouping")
    if depth:
        reject("EQUATION_LATEX_UNSUPPORTED", "unbalanced groups")
    return json.loads(_latex_cached(expression, element_id, font_size))
