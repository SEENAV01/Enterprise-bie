import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from auth import auth_context,authorized
from rate_limit import rate_limit_policy,within_limit
from idempotency import idempotency_record,reusable
from errors import status_for
from pagination import page
from gateway import route,route_match
from contract import validate_required

def test_auth():
 assert authorized(auth_context("u",["workflow:create"]),
                    "workflow:create")

def test_rate():
 assert within_limit(9,rate_limit_policy("x",10,60))

def test_idempotency():
 r=idempotency_record("k","hash",{}, "COMPLETED")
 assert reusable(r,"hash")

def test_errors_page_route():
 assert status_for("RATE_LIMITED")==429
 assert page(list(range(3)),2)["next_cursor"]=="2"
 assert route_match({"method":"GET","path":"/x"},
                    route("GET","/x","svc"))

def test_contract():
 assert validate_required({"name":"x"},["name"])
