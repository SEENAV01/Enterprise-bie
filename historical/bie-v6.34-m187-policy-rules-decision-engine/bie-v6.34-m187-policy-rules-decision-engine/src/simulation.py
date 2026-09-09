def simulate(policy, contexts):
    return [evaluate_policy(policy,c) for c in contexts]

def compare(before, after):
    return {"changed":[
        {"before":b,"after":a}
        for b,a in zip(before,after) if b!=a
    ]}
