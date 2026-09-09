import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from canonical import digest
from config import config_snapshot
from flags import feature_flag,flag_value
from experiments import assignment
from compatibility import compatibility
from versioning import bump

def test_deterministic_digest():
 assert digest({"b":2,"a":1})==digest({"a":1,"b":2})

def test_flag():
 f=feature_flag("x",enabled=True,default=False)
 assert flag_value(f)==True

def test_assignment():
 assert assignment("e","u")==assignment("e","u")

def test_compatibility():
 assert compatibility({"fps":30},{"fps":30})["compatible"]

def test_version():
 assert bump("1.2.3","minor")=="1.3.0"
