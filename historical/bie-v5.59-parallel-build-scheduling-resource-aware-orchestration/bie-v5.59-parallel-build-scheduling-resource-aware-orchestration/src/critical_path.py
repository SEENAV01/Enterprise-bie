def critical_path(jobs):
    by={j["job_id"]:j for j in jobs}
    memo={}
    def dur(jid):
        if jid in memo: return memo[jid]
        j=by[jid]
        parents=[d for d in j["dependencies"] if d in by]
        memo[jid]=j.get("estimated",{}).get("duration",0)+(
            max((dur(p) for p in parents),default=0))
        return memo[jid]
    for jid in by: dur(jid)
    return sorted(by,key=lambda x:memo[x],reverse=True),memo
