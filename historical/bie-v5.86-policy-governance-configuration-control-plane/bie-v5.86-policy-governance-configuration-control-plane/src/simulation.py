from decision import decision

def simulate(policy,contexts):
    return [{"context":c,"decision":decision(policy,c)}
            for c in contexts]

def diff_decisions(before,after):
    changes=[]
    for b,a in zip(before,after):
        if b["decision"]!=a["decision"]:
            changes.append({"before":b,"after":a})
    return changes
