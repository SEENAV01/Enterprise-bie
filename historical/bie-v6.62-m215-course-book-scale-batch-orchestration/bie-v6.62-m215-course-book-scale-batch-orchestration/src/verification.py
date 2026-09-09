def verification(i,b,status): return {"check_id":i,"batch_id":b,"status":status}
def passed(v): return v["status"]=="PASS"
