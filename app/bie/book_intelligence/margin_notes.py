
class MarginNoteError(ValueError):pass
def classify(box,page_width,main_left,main_right):
 x1,_,x2,_=box
 if not (0<=x1<x2<=page_width) or not (0<=main_left<main_right<=page_width):raise MarginNoteError("geometry")
 if x2<=main_left:return "LEFT_MARGIN"
 if x1>=main_right:return "RIGHT_MARGIN"
 return "MAIN_FLOW"
