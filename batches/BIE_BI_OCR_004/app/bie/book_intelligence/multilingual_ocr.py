
class LanguageError(ValueError):pass
def choose_languages(script_scores,limit=3):
 if limit<1:raise LanguageError("limit")
 xs=[(k,float(v)) for k,v in script_scores.items() if float(v)>0]
 if not xs:raise LanguageError("no script evidence")
 xs.sort(key=lambda x:(-x[1],x[0]))
 return tuple(k for k,_ in xs[:limit])
def validate_language_result(language,confidence):
 if not language or not 0<=confidence<=1:raise LanguageError("invalid language result")
 return True
