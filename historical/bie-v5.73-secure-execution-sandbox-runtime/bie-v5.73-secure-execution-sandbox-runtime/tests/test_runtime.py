import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from limits import resource_limits
from network import network_policy,network_allowed
from output import artifact_output,output_allowed
from sandbox import sandbox_spec
from compiler import validate_runtime

def test_network_default_deny():
 assert not network_allowed(network_policy("DENY"),"example.com")

def test_runtime_valid():
 s=sandbox_spec("x",resource_limits(),
   network_policy(),{"write_root":"/artifacts"},
   {"max_processes":2,"allowed_executables":["node"]})
 a=artifact_output("a","/artifacts/a","h","video/mp4",1000)
 assert validate_runtime(s,a,10)["valid"]

def test_output_limit():
 s=sandbox_spec("x",resource_limits(max_output_mb=1),
   network_policy(),{"write_root":"/artifacts"},
   {"max_processes":2,"allowed_executables":["node"]})
 a=artifact_output("a","/artifacts/a","h","video/mp4",2*1024*1024)
 assert not validate_runtime(s,a,10)["valid"]
