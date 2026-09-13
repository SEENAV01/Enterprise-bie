def review_schedule(index,mastery,count=3):
 if index<0 or not 0<=mastery<=1 or count<1: raise ValueError("inputs")
 base=1 if mastery<.6 else 2 if mastery<.85 else 3
 return tuple(index+base*(2**i) for i in range(count))
