def estimate_duration(concepts,complexity,practice,review_fraction=.15):
 if concepts<1 or complexity<=0 or practice<0: raise ValueError("inputs")
 subtotal=concepts*3*complexity+practice*2
 return subtotal*(1+review_fraction)
