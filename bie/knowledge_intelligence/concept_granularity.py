class E(ValueError):pass
LEVELS=("atomic","composite","topic","umbrella")
def classify(child_count,definition_count,scope_count):
 if min(child_count,definition_count,scope_count)<0:raise E("counts")
 if child_count>=5 or scope_count>=5:return "umbrella"
 if child_count>=2:return "composite"
 if definition_count>=1:return "atomic"
 return "topic"
