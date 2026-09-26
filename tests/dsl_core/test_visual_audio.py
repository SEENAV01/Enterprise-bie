import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.visual import *
from bie.game_engine.audio import *
class T(unittest.TestCase):
 def entity(self):return VisualEntity('e',VisualKind.OBJECT,'role',None,(),'desc')
 def test_visual(self):VisualExperienceContract((self.entity(),),(MotionCue('m','e',MotionKind.MOVE,0,100,'show change'),),(CameraCue('c',CameraKind.FOCUS,0,100,'focus learner','e'),)).validate()
 def test_visual_accessibility(self):
  with self.assertRaises(GameContractError):replace(self.entity(),accessible_description=None).validate()
 def test_motion_target(self):
  with self.assertRaises(GameContractError):MotionCue('m','x',MotionKind.MOVE,0,10,'why').validate({'e'})
 def test_motion_purpose(self):
  with self.assertRaises(GameContractError):MotionCue('m','e',MotionKind.MOVE,0,10,'').validate({'e'})
 def test_camera_requires_target(self):
  with self.assertRaises(GameContractError):CameraCue('c',CameraKind.ZOOM,0,10,'why').validate({'e'})
 def test_audio(self):AudioCue('a',AudioCueKind.SUCCESS,'done',asset_ref='asset:x').validate()
 def test_audio_source(self):
  with self.assertRaises(GameContractError):AudioCue('a',AudioCueKind.SUCCESS,'done').validate()
 def test_audio_duplicates(self):
  a=AudioCue('a',AudioCueKind.SUCCESS,'done',asset_ref='asset:x')
  with self.assertRaises(GameContractError):AudioExperienceContract((a,a)).validate()
