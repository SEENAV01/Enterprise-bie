def input_ref(input_id,hash_value,kind="DATA",
              version=None):
    return {"input_id":input_id,"hash":hash_value,
            "kind":kind,"version":version}

def verify_input(ref,current_hash):
    return ref.get("hash")==current_hash
