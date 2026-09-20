import unittest
from bie.scene_ir.text_element import build as text
from bie.scene_ir.equation_element import build as equation
from bie.scene_ir.vector_element import build as vector
from bie.scene_ir.graph_element import build as graph
from bie.scene_ir.map_element import build as mapel
from bie.scene_ir.simulation_element import build as simulation
from bie.scene_ir.scene_ir_contract import SceneTrack, SceneIR

class T(unittest.TestCase):
    def test_mixed_scene(self):
        elems=(
          text("txt","Force",("s",),("r",)),
          equation("eq","F=ma",("s",),("r",)),
          vector("vec",(3,4),("s",),("r",)),
          graph("g",({"points":[(0,0),(1,1)]},),("s",),("r",),x_label="t",y_label="x"),
          mapel("m","EPSG:4326",({"layer_id":"route","kind":"route"},),("s",),("r",)),
          simulation("sim","model:1",("s",),("r",),initial_state={}),
        )
        tracks=tuple(SceneTrack("tr:"+e.element_id,e.element_id,"reveal",0,100,{},("s",),("r",)) for e in elems)
        scene=SceneIR("scene","1.0.0","Mixed",100,elems,tracks,("s",),("r",))
        self.assertEqual(len(scene.elements),6)
        self.assertTrue(scene.ir_fingerprint)
        self.assertFalse(scene.accepted)
