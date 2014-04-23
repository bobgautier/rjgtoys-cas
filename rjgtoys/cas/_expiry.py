#
# expiry stuff
#

"""

Expiry times
============

Content items carry an expiry time: a time after which no CAS is obliged
to retain the item.

Internally, CAS uses epoch times to represent dates and times (see http://en.wikipedia.org/wiki/Epoch_time)

This format is convenient when dealing with most filesystems and makes working out expiry easy.

Constants
---------

.. autodata:: NEVER
.. autodata:: EXPIRED
.. autodata:: UNKNOWN

Functions
---------

.. autofunction:: expired
.. autofunction:: strepoch
.. autofunction:: expiry

Exceptions
----------

.. autoexception:: InvalidExpiryError

"""


import time
from _xc import CasErrorXC

class InvalidExpiryError(CasErrorXC):
    """Raised on an attempt to produce an expiry time from
    a string that cannot be parsed."""

    params=('expiry',)
    oneline = "Invalid expiry specification '{expiry}'"
    
# Never expires

def strepoch(s):
    """
    Converts a string in the form YYYY-mm-ddTHH:MM:SS into
    an epoch time
    
    Args:
        s: The string to be parsed.
        
    Returns:
        The corresponding expiry value.
        
    Raises:
        :exc:`InvalidExpiryError`
    """

    t = time.mktime(time.strptime(s,'%Y-%m-%dT%H:%M:%S'))
    
    return t

    
NEVER = strepoch('2008-03-19T00:00:00')
""" A special value that will never be considered to be :func:`expired` """

# Don't know

UNKNOWN = strepoch('2000-01-01T00:00:00')
""" A special value for expiry times that are unknown.   Like :data:`NEVER` this value never expires."""

# Always expired

EXPIRED = strepoch('1999-12-31T23:59:59')
""" A special value that has always expired. """


def expiry(e):
    """
    Convert almost anything to an expiry
    
    Args:
    
        e: Something to convert to an expiry.  Examples:
             an integer will be assumed to be a (positive) offset from
             the current time, in seconds
             
             a string in one of the following formats:
             YYYY-mm-ddTHH:MM:SS, YYYY-mm-ddTHH:MM, YYYY-mm-dd, HH:MM:SS, HH:MM
             
    Raises:
        :exc:`InvalidExpiryError`

    """
    
    try:
        x = int(e)
        if x < 0:
            raise InvalidExpiryError(expiry=e)
        # Anything less than our magic number is
        # assumed to be a relative expiry 
        if x < EXPIRED:
            x += int(time.time())
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
    """
    Tests whether an expiry has expired.
    
    Args:
        e: The expiry to be tested
        
    Returns:
        True iff e indicates a time in the past, or is the
            special value :data:`EXPIRED`.
    """

    if e == EXPIRED:
        return True
    if e == NEVER:
        return False
    if e == UNKNOWN:
        return False
        
    n = time.time()
    
    return e < n
    
def expire_relative(seconds=0,hours=0,minutes=0,days=0):
    """ Returns an expiry time that is the specified number
    of days, minutes, hours and seconds in the future."""
    
    offset = (((((days*24)+hours)*60)+minutes)*60)+seconds
    
    e = int(time.time()) + offset
    
    return e
