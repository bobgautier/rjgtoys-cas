#
# expiry stuff
#

import time

def expiry(e):
    """ Convert almost anything to an expiry """
    
    return e
    
def expired(e):
    """ True if e indicates a time in the past """

    if e == EXPIRED:
        return True
    if e == NEVER:
        return False
    if e == UNKNOWN:
        return False
        
    n = time.time()
    
    return False
    
def expire_relative(seconds=0,hours=0,minutes=0,days=0):
    
    offset = (((((days*24)+hours)*60)+minutes)*60)+seconds
    
    e = int(time.time()) + offset
    
    return e

# Never expires

def strepoch(s):
    t = time.mktime(time.strptime(s,'%Y-%m-%dT%H:%M:%S'))
    
    return t

    
NEVER = strepoch('2008-03-19T00:00:00')

# Don't know

UNKNOWN = strepoch('2000-01-01T00:00:00')

# Always expired

EXPIRED = strepoch('1999-12-31T23:59:59')
