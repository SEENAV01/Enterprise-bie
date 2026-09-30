"""H4-007: fresh-context observable replay; pixel equality is separately reported."""
from ..models import digest

def normalized(run):
    # No timing/process IDs are compared. Observed content/geometry/events and
    # checkpoint sequence ARE compared; missing actions cannot normalize away.
    return {'steps':run['steps'],'events':run['events']}

def compare(first,second):
    a=normalized(first);b=normalized(second)
    return {'matches':a==b,'first_sha256':digest(a),'second_sha256':digest(b),
        'screenshot_bytes_identical':first['screenshot']['sha256']==second['screenshot']['sha256'],
        'scope':'OBSERVED_SCENARIO_NOT_ARBITRARY_CODE_DETERMINISM'}
