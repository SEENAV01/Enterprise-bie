def review_item(item_id,priority,evidence,
                sla_seconds=None,required_role=None):
    return {"item_id":item_id,"priority":priority,
            "evidence":evidence,"sla_seconds":sla_seconds,
            "required_role":required_role,"status":"QUEUED"}

def enqueue(queue,item):
    queue.append(item)
    return len(queue)

def dequeue(queue):
    if not queue: return None
    queue.sort(key=lambda x:x.get("priority",0),reverse=True)
    item=queue.pop(0); item["status"]="IN_REVIEW"
    return item
