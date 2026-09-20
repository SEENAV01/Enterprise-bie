from .access_contracts import *
import re

HEX=re.compile(r"^#([0-9a-fA-F]{6})$")

def _rgb(hex_color):
    m=HEX.match(str(hex_color).strip())
    if not m: raise ContrastError("color must be #RRGGBB")
    s=m.group(1)
    return tuple(int(s[i:i+2],16)/255.0 for i in (0,2,4))

def _linear(c):
    return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4

def relative_luminance(hex_color):
    r,g,b=_rgb(hex_color)
    return 0.2126*_linear(r)+0.7152*_linear(g)+0.0722*_linear(b)

def contrast_ratio(foreground, background):
    l1,l2=relative_luminance(foreground),relative_luminance(background)
    hi,lo=max(l1,l2),min(l1,l2)
    return (hi+0.05)/(lo+0.05)

def evaluate_contrast(intent, *, foreground, background, large_text=False, enhanced=False):
    ratio=contrast_ratio(foreground,background)
    threshold=4.5
    if large_text: threshold=3.0
    if enhanced: threshold=4.5 if large_text else 7.0
    passed=ratio+1e-9>=threshold
    action="contrast_pass" if passed else "contrast_revise"
    return decision(intent,action=action,payload={"foreground":foreground.upper(),"background":background.upper(),
                    "ratio":round(ratio,4),"threshold":threshold,"large_text":bool(large_text),"enhanced":bool(enhanced),
                    "passes":passed},rationale=(f"ratio={ratio:.4f}",f"threshold={threshold:.1f}"),
                    warnings=() if passed else ("contrast_below_threshold",))
