#
# expiry stuff
#

import time
from _xc import CasErrorXC

class InvalidExpiryError(CasErrorXC):
    params=('expiry',)
    oneline = "Invalid expiry specification '{expiry}'"
    
# Never expires

def strepoch(s):
    t = time.mktime(time.strptime(s,'%Y-%m-%dT%H:%M:%S'))
    
    return t

    
NEVER = strepoch('2008-03-19T00:00:00')

# Don't know

UNKNOWN = strepoch('2000-01-01T00:00:00')

# Always expired

EXPIRED = strepoch('1999-12-31T23:59:59')


def expiry(e):
    """ Convert almost anything to an expiry """
    
    try:
        x = int(e)
        if x < 0:
            raise InvalidExpiryError(expiry=e)
        return x
    except:
        pass
        
    # See if it's a string
    
    if not isinstance(e,basestring):
        raise InvalidExpiryError(expiry=e)
    
    x = None
    for fmt in ("%Y-%m-%dT%H:%M:%S","%Y-%m-%dT%H:%M","%Y-%m-%d","%H:%M:%S","%H:%M"):
        try:
            x = time.mktime(time.strptime(e,fmt))
        except:
            continue
    if x is None:
        raise InvalidExpiryError(expiry=e)
        
    return x
    
def expired(e):
    """ True if e indicates a time in the past """

    if e == EXPIRED:
        return True
    if e == NEVER:
        return False
    if e == UNKNOWN:
        return False
        
    n = time.time()
    
    return e < n
    
def expire_relative(seconds=0,hours=0,minutes=0,days=0):
    
    offset = (((((days*24)+hours)*60)+minutes)*60)+seconds
    
    e = int(time.time()) + offset
    
    return e
