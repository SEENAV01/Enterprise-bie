from .representation_core import *
def choose(intent,event_count,has_order=True,has_intervals=False,uncertain_dates=False,simultaneous_events=False):
 if isinstance(event_count,bool) or not isinstance(event_count,int) or event_count<0:raise RepresentationError('event_count')
 need=intent.temporal or event_count>=2 or 'chronology' in intent.semantic_tags
 if not need:return decision(intent,None,'UNSUPPORTED',.95,('no_temporal_structure',),suffix='timeline')
 if event_count<2 or not has_order:return decision(intent,None,'REVIEW',.5,('insufficient_ordered_events',),{'event_count':event_count},'timeline')
 return decision(intent,'timeline','PASS',max(.5,.92-intent.uncertainty*.2-(.05 if uncertain_dates else 0)),('ordered_events_benefit_from_timeline',),{'event_count':event_count,'intervals':has_intervals,'uncertain_dates':uncertain_dates,'simultaneous_events':simultaneous_events,'preserve_uncertainty':uncertain_dates},'timeline')
