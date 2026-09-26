from __future__ import annotations
from .planner import plan_experience
from .studio_policy import audit_studio_quality
from .receipts import create_director_receipt
from ..canonical import fingerprint

def run_director_pipeline(ctx):
    plan=plan_experience(ctx);policy=audit_studio_quality(plan);receipt=create_director_receipt(plan,policy)
    return {'schema_version':'bie.game.director-pipeline/2','plan':plan,'plan_fingerprint':plan.plan_fingerprint,'studio_policy':policy,'receipt':receipt,'deterministic_receipt':receipt.receipt_fingerprint,'product_accepted':False}
