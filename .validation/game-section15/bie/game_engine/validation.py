from __future__ import annotations
import inspect
from .document import GameDocument
from .codec import dumps,loads
from .receipts import make_receipt
from .errors import GameContractError

def validate_game_document(document:GameDocument):
    if type(document) is not GameDocument:raise GameContractError('GAME_DOCUMENT_TYPE')
    document.validate();wire=dumps(document);roundtrip=loads(wire)
    if roundtrip!=document:raise GameContractError('GAME_WIRE_ROUNDTRIP')
    output={'schema_version':'bie.game.dsl.validation/2','document_id':document.document_id,'game_ir_version':document.game_ir_version,'document_fingerprint':document.fingerprint(),'wire_bytes':len(wire),'wire_roundtrip':True,'studio_grade_intent':True,'anti_slide_default':True,'product_accepted':False}
    receipt=make_receipt('BIE-GAME-DSL-001',document,output,inspect.getsource(validate_game_document))
    return output,receipt
