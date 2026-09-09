def calibrate(raw,bins):
 if not 0<=raw<=1:raise ValueError("raw")
 m=[b for b in bins if b[0]<=raw<=b[1]]
 if not m:return raw
 b=min(m,key=lambda x:x[1]-x[0])
 if not 0<=b[2]<=1:raise ValueError("accuracy")
 return b[2]
