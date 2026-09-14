from dataclasses import dataclass
@dataclass(frozen=True)
class PersonaDecision: persona:str; tone:str; rationale:str
def select_persona(age_band,content_type,lesson_mode):
    if not age_band.strip() or not content_type.strip() or not lesson_mode.strip(): raise ValueError("inputs")
    if lesson_mode=="INQUIRY":return PersonaDecision("SOCRATIC_GUIDE","curious","guided discovery")
    if lesson_mode=="DERIVATION":return PersonaDecision("EXPERT_TUTOR","precise","stepwise reasoning")
    if content_type in {"NARRATIVE","INTERPRETIVE","SOURCE_CRITICISM"}:return PersonaDecision("DOCUMENTARY_NARRATOR","reflective","evidence-sensitive storytelling")
    if age_band in {"EARLY_PRIMARY","PRIMARY"}:return PersonaDecision("FRIENDLY_COACH","warm","age appropriate")
    return PersonaDecision("EXPERT_GUIDE","clear","default")
