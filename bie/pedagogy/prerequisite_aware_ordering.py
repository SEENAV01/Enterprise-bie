from bie.pedagogy.lesson_sequencing import sequence_lessons
def prerequisite_order(items,edges,threshold=.5):
 return sequence_lessons(items,[(a,b) for a,b,s in edges if s>=threshold])
