def sequence(entity_id,next_sequence=0):
    return {"entity_id":entity_id,
            "next_sequence":next_sequence}

def accept(record,sequence_number):
    expected=record["next_sequence"]
    if sequence_number != expected:
        return False
    record["next_sequence"]=expected+1
    return True
