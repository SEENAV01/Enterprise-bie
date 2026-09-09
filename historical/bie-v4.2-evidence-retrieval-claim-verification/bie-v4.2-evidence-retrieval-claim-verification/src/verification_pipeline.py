from claim_extractor import extract_claims
from evidence_packet import build_packet
from verification import verify_packet
from retrieval_contract import retrieval_request
from source_ranker import rank_sources

def prepare_verification(item, sources=None, evidences=None):
    claims=extract_claims(item)
    ranked=rank_sources(sources or [])
    packet=build_packet(item,claims,evidences or [])
    packet=verify_packet(packet)
    return {
      "schema_version":"4.2",
      "knowledge_id":item["id"],
      "retrieval_request":retrieval_request(item),
      "ranked_sources":ranked,
      "evidence_packet":packet
    }
