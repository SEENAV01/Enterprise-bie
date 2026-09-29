"""Exact axis-aligned rectangle diagnostics. No sampling or group exemptions."""
from fractions import Fraction
from ..release_v2.contracts import ContractError, integer
from .models import Rect, RGBA


def contains(outer, inner, tolerance=0):
    integer(tolerance,'tolerance',0,1000)
    return inner.x>=outer.x-tolerance and inner.y>=outer.y-tolerance and inner.right<=outer.right+tolerance and inner.bottom<=outer.bottom+tolerance


def intersection(a,b):
    x,y=max(a.x,b.x),max(a.y,b.y); right,bottom=min(a.right,b.right),min(a.bottom,b.bottom)
    return Rect(x,y,right-x,bottom-y) if right>x and bottom>y else None


def union_area(rectangles):
    """Sweep x boundaries; merge y intervals exactly. Duplicate boxes add no area."""
    boxes=tuple(rectangles)
    if len(boxes)>512 or any(type(r) is not Rect for r in boxes): raise ContractError('VIS_UNION_LIMIT_OR_TYPE')
    xs=sorted({x for r in boxes for x in (r.x,r.right)})
    area=0
    for a,b in zip(xs,xs[1:]):
        spans=sorted((r.y,r.bottom) for r in boxes if r.x<b and r.right>a)
        length=0; end=None
        for y,z in spans:
            if end is None or y>end: length+=z-y; end=z
            elif z>end: length+=z-end; end=z
        area+=(b-a)*length
    return area


def area_ppm(rectangles, bounds):
    clips=[intersection(r,bounds) for r in rectangles]
    return Fraction(union_area(r for r in clips if r is not None)*1000000, bounds.area)


def gap_squared(a,b):
    dx=max(0,a.x-b.right,b.x-a.right);dy=max(0,a.y-b.bottom,b.y-a.bottom)
    return dx*dx+dy*dy


def grid_peak(boxes,bounds,rows,columns):
    integer(rows,'rows',1,10);integer(columns,'columns',1,10)
    peak=0
    for y in range(rows):
        for x in range(columns):
            a=bounds.x+bounds.width*x//columns;b=bounds.x+bounds.width*(x+1)//columns
            c=bounds.y+bounds.height*y//rows;d=bounds.y+bounds.height*(y+1)//rows
            if a==b or c==d: continue
            cell=Rect(a,c,b-a,d-c)
            peak=max(peak,sum(intersection(r,cell) is not None for r in boxes))
    return peak


def contrast_ratio(foreground,background,opacity_ppm=1000000):
    """W3C sRGB relative-luminance formula, unrounded comparison.

    Only a known opaque, uniform background is supported. CSS filters, blends,
    gradients and images require another evaluator, not an assumed average color.
    Reference: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
    """
    if type(foreground) is not RGBA or type(background) is not RGBA or background.a!=255:
        raise ContractError('VIS_CONTRAST_BACKGROUND_UNKNOWN')
    integer(opacity_ppm,'opacity_ppm',0,1000000)
    alpha=Fraction(foreground.a*opacity_ppm,255*1000000)
    fg=[float((alpha*f+(1-alpha)*b)/255) for f,b in zip((foreground.r,foreground.g,foreground.b),(background.r,background.g,background.b))]
    bg=[x/255 for x in (background.r,background.g,background.b)]
    def luminance(channels):
        linear=[x/12.92 if x<=0.04045 else ((x+0.055)/1.055)**2.4 for x in channels]
        return sum(c*w for c,w in zip(linear,(0.2126,0.7152,0.0722)))
    a,b=sorted((luminance(fg),luminance(bg)))
    return (b+0.05)/(a+0.05)
