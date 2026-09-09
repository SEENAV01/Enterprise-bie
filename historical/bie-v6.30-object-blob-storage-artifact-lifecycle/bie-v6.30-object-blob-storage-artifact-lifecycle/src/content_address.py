def content_address(hash_value,
                    algorithm="SHA256"):
    return {"algorithm":algorithm,
            "hash":hash_value,
            "address":f"{algorithm}:{hash_value}"}

def same_content(a,b):
    return a["address"]==b["address"]
