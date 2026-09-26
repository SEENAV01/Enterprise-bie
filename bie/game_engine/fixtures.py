from .provenance import EvidenceRef,ProvenanceBundle
from .learning import LearningTarget
from .state import StateVariableSpec,StateModel
from .expressions import *
from .interaction import *
from .visual import *
from .audio import *
from .feedback import FeedbackContract
from .adaptation import *
from .quality_intent import *
from .document import *

def evidence():
    h='0'*64
    return ProvenanceBundle((EvidenceRef('source:book','page:10',h,'source'),EvidenceRef('reason:game','decision:1',h,'reasoning'),EvidenceRef('objective:motion','lo:1',h,'objective')))

def sample_document():
    prov=evidence();learning=LearningTarget('obj:motion',('concept:motion',),('pre:position',),('mis:direction',),0.8,prov)
    state=StateModel((StateVariableSpec('x',ValueType.NUMBER,1.0,0,10,units='m',semantic_role='position'),StateVariableSpec('attempts',ValueType.INTEGER,0,0,10,semantic_role='attempt_count')))
    actions=(ActionSpec('drag:mover',ActionKind.DRAG,'entity:mover','Move the object','Arrow keys adjust position'),ActionSpec('submit',ActionKind.SUBMIT,'entity:mover','Submit answer'))
    rule=RuleSpec('rule:move',Compare(CompareOp.LT,Variable('x'),Literal(2)),(EffectSpec('x',EffectKind.SET,2.0),),'Moving changes the position.',10,('source:book',))
    interaction=InteractionContract(actions,(rule,))
    visual=VisualExperienceContract((VisualEntity('entity:mover',VisualKind.OBJECT,'manipulated_object','source:book',('x',),'A movable object'),VisualEntity('entity:target',VisualKind.LABEL,'target_marker','source:book',(), 'Target at x equals 2')), (MotionCue('motion:move','entity:mover',MotionKind.MOVE,0,800,'Show the state change caused by learner manipulation'),),(CameraCue('camera:focus',CameraKind.FOCUS,0,800,'Keep learner attention on the changing object','entity:mover'),))
    audio=AudioExperienceContract((AudioCue('audio:success',AudioCueKind.SUCCESS,'challenge_success',asset_ref='asset:sfx:success'),))
    feedback=FeedbackContract('text:success','text:failure',(('mis:direction','text:misdirection'),),'text:explanation',False)
    adaptation=AdaptationContract((AdaptationRule('adapt:hint',Compare(CompareOp.GE,Variable('attempts'),Literal(2)),AdaptAction.UNLOCK_HINT,1,'hint:2'),))
    challenge=ChallengeContract('challenge:motion','Move to target','text:mission:motion',ExperienceMode.MANIPULATION,learning,Compare(CompareOp.EQ,Variable('x'),Literal(2)),(Compare(CompareOp.GT,Variable('attempts'),Literal(3)),),feedback,0.35,1.0)
    level=GameLevelContract('level:1','Motion Lab','Build intuitive displacement understanding',state,interaction,visual,audio,adaptation,(challenge,))
    exp=GameExperienceContract('game:motion','Motion Revision Lab',(level,),'policy:score:v1','policy:mastery:v1')
    return GameDocument('2.0.0','game-doc:motion',(exp,),prov,False)
