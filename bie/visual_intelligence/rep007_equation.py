from .representation_core import *
def choose(intent,expression,derivation_steps=0,tokenized=True,narration_sync_available=False,morph_requested=False,semantic_token_map=None):
 if not isinstance(expression,str) or not expression.strip():raise RepresentationError('expression required')
 if isinstance(derivation_steps,bool) or not isinstance(derivation_steps,int) or derivation_steps<0:raise RepresentationError('derivation_steps')
 need=intent.equation_present or 'equation' in intent.semantic_tags or derivation_steps>0
 if not need:return decision(intent,None,'UNSUPPORTED',.95,('equation_not_instructionally_material',),suffix='equation')
 if morph_requested and (not tokenized or not semantic_token_map):return decision(intent,'equation','REVIEW',.6,('equation_morph_requires_semantic_token_mapping',),{'expression':expression,'morph_allowed':False},'equation')
 return decision(intent,'equation','PASS',.95-intent.uncertainty*.1,('equation_state_is_semantically_grounded',),{'expression':expression,'derivation_steps':derivation_steps,'tokenized':tokenized,'narration_sync_available':narration_sync_available,'morph_allowed':bool(morph_requested and semantic_token_map),'states':max(1,derivation_steps+1)},'equation')
