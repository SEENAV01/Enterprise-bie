from dataclasses import replace
from bie.director.script_plan import ScriptSegment,build_script_plan
from bie.director.voiceover_generation import generate_voiceover,VoiceoverDraft
from bie.director.speech_timing import utterances_from_script
from bie.audio.lexicon import build_lexicon
from bie.audio.symbol_pronunciation import standard_symbols
from bie.audio.acronym_pronunciation import make_acronyms,AcronymRule

def director(text='The force acts along the line.',language='en',sid='s1'):
    script=build_script_plan('lesson:synthetic',(ScriptSegment(sid,'scene:one','EXPLAIN','Describe the relation',('source:p1',),('objective:one',)),),'voice:teacher')
    draft=generate_voiceover(sid,(text,),{text:('source:p1',)})
    return script,(draft,),(sid,),tuple(utterances_from_script(script,(draft,),(sid,),language))

def utterance(text='The force acts along the line.',language='en'):
    return director(text,language)[3][0]

def empty_options(language='en'):
    return dict(lexicon=build_lexicon('empty/1',()),symbols=standard_symbols(language),acronyms=make_acronyms('empty/1',()))
