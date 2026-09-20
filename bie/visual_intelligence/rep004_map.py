from .representation_core import *
def choose(intent,has_geographic_coordinates=False,has_route=False,has_region_membership=False,crs=None,spatial_relation_only=False):
 need=intent.spatial or has_geographic_coordinates or has_route or has_region_membership or 'geographic' in intent.semantic_tags
 if not need:return decision(intent,None,'UNSUPPORTED',.95,('no_geographic_semantics',),suffix='map')
 if has_geographic_coordinates and not crs:return decision(intent,None,'BLOCKED',.3,('coordinates_require_crs',),suffix='map')
 if spatial_relation_only and not (has_geographic_coordinates or has_route or has_region_membership):return decision(intent,'diagram','REVIEW',.7,('abstract_spatial_relation_better_as_diagram',),suffix='map')
 return decision(intent,'map','PASS',.92-intent.uncertainty*.2,('map_preserves_geographic_semantics',),{'crs':crs,'route':has_route,'regions':has_region_membership},'map')
