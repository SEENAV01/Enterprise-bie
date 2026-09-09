import unittest
from dataclasses import replace
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.map_reasoning import MapFrame, MapLocation, MapEdge, relative_position, shortest_route

class MapTests(unittest.TestCase):
    def setUp(self):
        self.refs = (EvidenceRef("map:1", "primary", .9),)
        self.f = MapFrame("diagram:1", 100, ("map:1",))
        self.a = MapLocation("A", 0, 0, ("map:1",))
        self.b = MapLocation("B", 3, 4, ("map:1",))

    def edge(self, name, a, b, cost, two=False):
        return MapEdge(name, a, b, cost, ("map:1",), two)

    def test_scaled_345(self):
        r = relative_position(self.f, self.a, self.b, self.refs)
        self.assertEqual(r.value["distance_m"], 500)
        self.assertEqual(r.value["east_m"], 300)
        self.assertEqual(r.value["north_m"], 400)
        self.assertAlmostEqual(r.value["bearing_degrees_clockwise_from_north"], 36.86989764584402)

    def test_screen_axis(self):
        r = relative_position(replace(self.f, y_axis="south"), self.a, self.b, self.refs)
        self.assertEqual(r.value["direction"], "SE")

    def test_coincident_locations(self):
        r = relative_position(self.f, self.a, replace(self.b, x=0, y=0), self.refs)
        self.assertIsNone(r.value["bearing_degrees_clockwise_from_north"])

    def test_cardinal_bearings(self):
        for x, y, direction, bearing in [(0,1,"N",0),(1,0,"E",90),(0,-1,"S",180),(-1,0,"W",270)]:
            with self.subTest(direction=direction):
                v=relative_position(self.f,self.a,replace(self.b,x=x,y=y),self.refs).value
                self.assertEqual((v["direction"],v["bearing_degrees_clockwise_from_north"]),(direction,bearing))

    def test_missing_source(self):
        with self.assertRaises(ValueError): relative_position(self.f,self.a,self.b,())

    def test_dangling_source(self):
        with self.assertRaises(ValueError): relative_position(self.f,self.a,replace(self.b,evidence_ids=("unknown",)),self.refs)

    def test_invalid_scales(self):
        for x in (0,-1,float("nan"),float("inf"),True):
            with self.subTest(x=x), self.assertRaises(ValueError): relative_position(replace(self.f,metres_per_unit=x),self.a,self.b,self.refs)

    def test_coordinate_system_not_guessed(self):
        with self.assertRaises(ValueError): relative_position(replace(self.f,coordinate_system="EPSG:4326"),self.a,self.b,self.refs)

    def test_route_uses_network_costs(self):
        c=MapLocation("C",10,10,("map:1",));edges=[self.edge("AB","A","B",20),self.edge("AC","A","C",4),self.edge("CB","C","B",5)]
        r=shortest_route(self.f,[self.a,self.b,c],edges,"A","B",self.refs)
        self.assertEqual(r.value,{"distance_m":9.0,"edge_ids":["AC","CB"],"node_ids":["A","C","B"]})

    def test_one_way_unreachable(self):
        r=shortest_route(self.f,[self.a,self.b],[self.edge("AB","A","B",5)],"B","A",self.refs)
        self.assertEqual(r.status,"UNREACHABLE");self.assertTrue(r.requires_review)

    def test_bidirectional(self):
        r=shortest_route(self.f,[self.a,self.b],[self.edge("AB","A","B",5,True)],"B","A",self.refs)
        self.assertEqual(r.value["node_ids"],["B","A"])

    def test_start_goal_same(self):
        r=shortest_route(self.f,[self.a],[],"A","A",self.refs)
        self.assertEqual(r.value["distance_m"],0);self.assertEqual(r.value["node_ids"],["A"])

    def test_tie_determinism(self):
        c=MapLocation("C",1,1,("map:1",));d=MapLocation("D",2,2,("map:1",));locs=[self.a,self.b,c,d]
        edges=[self.edge("AC","A","C",1),self.edge("CD","C","D",1),self.edge("AB","A","B",1),self.edge("BD","B","D",1)]
        x=shortest_route(self.f,locs,edges,"A","D",self.refs);y=shortest_route(self.f,list(reversed(locs)),list(reversed(edges)),"A","D",self.refs)
        self.assertEqual(x.result_id,y.result_id);self.assertEqual(x.value["node_ids"],["A","B","D"])

    def test_invalid_edges_and_nodes(self):
        for edge in [self.edge("x","A","Q",1),self.edge("x","A","A",1),self.edge("x","A","B",0),self.edge("x","A","B",float("nan"))]:
            with self.subTest(edge=edge),self.assertRaises(ValueError):shortest_route(self.f,[self.a,self.b],[edge],"A","B",self.refs)

    def test_duplicate_identity(self):
        with self.assertRaises(ValueError):shortest_route(self.f,[self.a,self.a],[],"A","A",self.refs)

    def test_input_immutability(self):
        locs=[self.a,self.b];edges=[self.edge("AB","A","B",5)];original=(locs[:],edges[:])
        shortest_route(self.f,locs,edges,"A","B",self.refs);self.assertEqual((locs,edges),original)
