from .representation_core import *
def choose(intent,data_points=0,function_defined=False,axis_semantics=False,units_known=False,sampled_data=False,exact_curve_claim=False,domain_restriction=False):
 if isinstance(data_points,bool) or not isinstance(data_points,int) or data_points<0:raise RepresentationError('data_points')
 need=intent.quantitative or data_points>=2 or function_defined or 'graph' in intent.semantic_tags
 if not need:return decision(intent,None,'UNSUPPORTED',.95,('no_quantitative_relation',),suffix='graph')
 if not axis_semantics:return decision(intent,None,'BLOCKED',.35,('axis_semantics_required',),suffix='graph')
 if sampled_data and exact_curve_claim:return decision(intent,None,'BLOCKED',.2,('sampled_data_cannot_be_claimed_exact_curve',),suffix='graph')
 status='PASS' if units_known or not intent.payload.get('units_required',False) else 'REVIEW'
 return decision(intent,'graph',status,.90-intent.uncertainty*.15,('graph_preserves_quantitative_relation',),{'data_points':data_points,'function_defined':function_defined,'units_known':units_known,'sampled_data':sampled_data,'domain_restriction':domain_restriction},'graph')
