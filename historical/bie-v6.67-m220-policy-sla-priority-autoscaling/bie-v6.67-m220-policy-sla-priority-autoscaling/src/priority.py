CLASSES={"CRITICAL":4,"HIGH":3,"NORMAL":2,"LOW":1}
def priority_score(job,now=0):
    base=CLASSES.get(job.get("priority_class","NORMAL"),2)
    age=max(0,now-job.get("queued_at",0))
    deadline=job.get("deadline_seconds")
    urgency=0 if deadline is None else max(0,deadline-(now-job.get("queued_at",0)))
    return base*1000+age-urgency
def rank(jobs,now=0):
    return sorted(jobs,key=lambda j:priority_score(j,now),reverse=True)
