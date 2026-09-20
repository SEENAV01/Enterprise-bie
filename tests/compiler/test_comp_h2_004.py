from copy import deepcopy
import math,unittest
from bie.compiler.map_geometry import *
from bie.compiler.map_compiler import compile_map_element
from bie.compiler.generated_code_regression import probe_typescript_sources
from tests.compiler.h2_test_support import element,geo_props,runtime,nodes,text_nodes

class GeographicProjectionTests(unittest.TestCase):
    def bad(self,change,code='MAP|COLLECTION|UNCONSUMED|NUMERIC|TEXT'):
        p=geo_props();change(p)
        with self.assertRaisesRegex(ValueError,code):map_geometry(p)
    def test_mercator_matches_published_proj_example(self):
        x,y=project_lonlat(2,49,'web_mercator');self.assertAlmostEqual(x,222638.98158654713,7);self.assertAlmostEqual(y,6274861.394006576,6)
    def test_mercator_matches_independent_pyproj(self):
        from pyproj import Transformer
        tr=Transformer.from_crs(4326,3857,always_xy=True)
        for lon,lat in [(-120,-60),(-20,-30),(0,0),(65,23),(175,80)]:
            a=project_lonlat(lon,lat,'web_mercator');b=tr.transform(lon,lat)
            for x,y in zip(a,b):self.assertAlmostEqual(x,y,6)
    def test_equirectangular_matches_independent_pyproj(self):
        from pyproj import Proj
        p=Proj('+proj=eqc +lat_ts=0 +R=6378137')
        for lon,lat in [(2,49),(-70,-20),(0,0)]:
            for a,b in zip(project_lonlat(lon,lat,'equirectangular'),p(lon,lat)):self.assertAlmostEqual(a,b,7)
    def test_equator_origin_exact(self):self.assertEqual(project_lonlat(0,0,'web_mercator'),(0.,0.))
    def test_hemisphere_signs_preserved(self):
        x,y=project_lonlat(-2,-49,'web_mercator');self.assertLess(x,0);self.assertLess(y,0)
    def test_projection_changes_actual_geometry(self):
        a=map_geometry(geo_props());b=map_geometry(geo_props('equirectangular'));self.assertNotEqual(a.layers[0]['pixels'],b.layers[0]['pixels'])
    def test_latitude_nonlinearity_visible(self):
        low=project_lonlat(0,20,'web_mercator')[1];mid=project_lonlat(0,40,'web_mercator')[1];hi=project_lonlat(0,60,'web_mercator')[1];self.assertGreater(hi-mid,mid-low)
    def test_original_geographic_coordinates_retained(self):
        p=geo_props();g=map_geometry(p);self.assertEqual(g.layers[0]['source_points'],p['layers'][0]['points'])
    def test_projected_coordinates_retained(self):
        g=map_geometry(geo_props());self.assertEqual(g.layers[0]['projected_points'][1],list(project_lonlat(0,40,'web_mercator')))
    def test_undistorted_projected_aspect_ratio(self):
        p=geo_props('equirectangular');p['projection']['extent']=[-10,-10,10,10];p['layers'][0]['points']=[[-5,0],[0,0],[0,5]];q=map_geometry(p).layers[0]['pixels'];self.assertAlmostEqual(q[1][0]-q[0][0],q[1][1]-q[2][1])
    def test_normalized_old_contract_supported(self):
        g=map_geometry({'crs':'BIE:NORMALIZED','layers':[{'kind':'route','points':[[0,0],[1,1]]}]});self.assertEqual(g.axis_order,'xy');self.assertGreater(g.layers[0]['pixels'][0][1],g.layers[0]['pixels'][1][1])
    def test_point_layer_really_drawn(self):
        p=geo_props();p['layers']=[{'kind':'point','points':[[0,40]],'label':'point'}];tree=runtime(compile_map_element(element('map',p)))['trees'][0]['tree'];self.assertEqual(len(nodes(tree,'circle')),1)
    def test_polygon_layer_really_drawn(self):
        p=geo_props();p['layers']=[{'kind':'polygon','points':[[-5,30],[5,30],[0,50],[-5,30]],'label':'triangle'}];tree=runtime(compile_map_element(element('map',p)))['trees'][0]['tree'];self.assertEqual(len(nodes(tree,'polygon')),1)
    def test_each_mixed_layer_drawn(self):
        p=geo_props();p['layers'] += [{'kind':'point','points':[[0,40]],'label':'point'},{'kind':'polygon','points':[[-5,30],[5,30],[0,50],[-5,30]],'label':'area'}];t=runtime(compile_map_element(element('map',p)))['trees'][0]['tree'];self.assertEqual(len(nodes(t,'circle')),1);self.assertEqual(len(nodes(t,'polyline')),1);self.assertEqual(len(nodes(t,'polygon')),1)
    def test_attribution_visible(self):
        p=geo_props();t=runtime(compile_map_element(element('map',p)))['trees'][0]['tree'];self.assertIn(p['attribution'],text_nodes(t))
    def test_coordinate_order_required(self):self.bad(lambda p:p['projection'].pop('axis_order'),'PROJECTION_REQUIRED')
    def test_latlon_not_silently_swapped(self):self.bad(lambda p:p['projection'].update(axis_order='lat_lon'),'PROJECTION_UNSUPPORTED')
    def test_projection_not_inferred_from_crs(self):self.bad(lambda p:p.pop('projection'),'PROJECTION_REQUIRED')
    def test_unknown_crs_blocked(self):self.bad(lambda p:p.update(crs='EPSG:32643'),'SOURCE_CRS')
    def test_malformed_crs_blocked(self):self.bad(lambda p:p.update(crs={}), 'SOURCE_CRS')
    def test_unknown_projection_blocked(self):self.bad(lambda p:p['projection'].update(kind='arbitrary'),'PROJECTION_UNSUPPORTED')
    def test_mercator_poles_not_clamped(self):
        with self.assertRaisesRegex(ValueError,'LATITUDE_LIMIT'):project_lonlat(0,90,'web_mercator')
    def test_lon_out_of_range_blocked(self):
        with self.assertRaises(ValueError):project_lonlat(190,0,'web_mercator')
    def test_nan_coordinate_blocked(self):
        with self.assertRaises(ValueError):project_lonlat(float('nan'),0,'web_mercator')
    def test_extent_clipping_not_silent(self):self.bad(lambda p:p['layers'][0]['points'].append([30,40]),'OUTSIDE_EXTENT')
    def test_antimeridian_route_not_drawn_across_world(self):
        p=geo_props();p['projection']['extent']=[-180,-60,180,60];p['layers'][0]['points']=[[179,0],[-179,0]]
        with self.assertRaisesRegex(ValueError,'ANTIMERIDIAN'):map_geometry(p)
    def test_wrapped_extent_not_reinterpreted(self):self.bad(lambda p:p['projection'].update(extent=[170,-10,-170,10]),'EXTENT_INVALID')
    def test_zero_extent_rejected(self):self.bad(lambda p:p['projection'].update(extent=[0,30,0,50]),'EXTENT_INVALID')
    def test_extremely_small_extent_rejected(self):self.bad(lambda p:p['projection'].update(extent=[0,30,1e-10,50]),'EXTENT_UNRESOLVED')
    def test_remote_tile_layer_not_ignored(self):self.bad(lambda p:p['layers'].append({'kind':'raster','points':[[0,0]]}),'LAYER_UNSUPPORTED')
    def test_duplicate_layer_identity_rejected(self):
        self.bad(lambda p:p['layers'].extend([{'kind':'point','layer_id':'x','points':[[0,40]]},{'kind':'point','layer_id':'x','points':[[1,40]]}]),'ID_DUPLICATE')
    def test_polygon_must_be_explicitly_closed(self):self.bad(lambda p:p.update(layers=[{'kind':'polygon','points':[[-5,30],[5,30],[0,50]]}]),'POLYGON_INVALID')
    def test_self_crossing_polygon_rejected(self):self.bad(lambda p:p.update(layers=[{'kind':'polygon','points':[[-8,25],[8,55],[-8,55],[8,30],[-8,25]]}]),'POLYGON')
    def test_missing_attribution_rejected(self):self.bad(lambda p:p.pop('attribution'),'TEXT_VALUE_INVALID')
    def test_unconsumed_altitude_rejected(self):self.bad(lambda p:p['layers'][0]['points'].append([0,40,100]),'COLLECTION_SHAPE')
    def test_projected_source_ast_passes(self):
        r=compile_map_element(element('map',geo_props()));self.assertEqual(probe_typescript_sources(((r.source_path,r.source_text),)).status,'PASS')
    def test_geo_renderer_not_accepted(self):self.assertFalse(compile_map_element(element('map',geo_props())).accepted)

if __name__=='__main__':unittest.main()
