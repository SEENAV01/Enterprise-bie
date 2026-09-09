from content_address import content_id

def integrity_check(data,expected_content_id):
    actual=content_id(data)
    return {"expected":expected_content_id,
            "actual":actual,"valid":actual==expected_content_id}
