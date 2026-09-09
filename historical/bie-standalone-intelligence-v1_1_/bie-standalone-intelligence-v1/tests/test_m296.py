import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from m296_rerender_regression import regression_decision

def test_accept_verified_zero_mismatch():
    d=regression_decision({"mismatch_count":1},{"status":"verified","mismatch_count":0})
    assert d["decision"]=="accept"

def test_reject_remaining_mismatch():
    d=regression_decision({"mismatch_count":1},{"status":"mismatch","mismatch_count":1})
    assert d["decision"]=="reject"

def test_review_not_proven():
    d=regression_decision({"mismatch_count":1},{"status":"not_proven","mismatch_count":0})
    assert d["decision"]=="review"
