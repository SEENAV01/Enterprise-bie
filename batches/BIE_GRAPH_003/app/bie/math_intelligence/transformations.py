from dataclasses import dataclass
@dataclass(frozen=True)
class Transformation:
 kind:str; parameter:float; description:str
def transformations(a=1.0,h=0.0,k=0.0)->tuple[Transformation,...]:
 out=[]
 if a<0:out.append(Transformation("reflection_x",a,"reflect across x-axis"))
 if abs(a)!=1:out.append(Transformation("vertical_scale",abs(a),f"vertical scale by {abs(a)}"))
 if h:out.append(Transformation("horizontal_shift",h,f"shift {'right' if h>0 else 'left'} by {abs(h)}"))
 if k:out.append(Transformation("vertical_shift",k,f"shift {'up' if k>0 else 'down'} by {abs(k)}"))
 return tuple(out)
