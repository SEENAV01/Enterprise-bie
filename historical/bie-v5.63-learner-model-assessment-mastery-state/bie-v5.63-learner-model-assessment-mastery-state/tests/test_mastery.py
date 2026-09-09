import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from mastery import classify_mastery
from remediation import recommend_remediation

def test_mastered():
 assert classify_mastery(.9,.1)=="MASTERED"

def test_support():
 s={"estimate":.4,"uncertainty":.2}
 r={"threshold":.5,"uncertainty":.35,"strategies":["PRACTICE"]}
 assert recommend_remediation(s,r)==["PRACTICE"]
