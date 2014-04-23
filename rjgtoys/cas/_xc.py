#
# exceptions associated with cas
#

"""

Exceptions
==========

Errors
------

.. autoexception:: ItemNotFoundError
.. autoexception:: ItemCorruptedError

Exception Classes
-----------------

The above exceptions are derived from the following base classes.

.. autoexception:: CasXC
.. autoexception:: CasErrorXC


"""

from rjgtoys import xc

class CasXC(xc.BaseXC):
    """ This is the base class of all CAS-related exceptions """
    
    pass
    
class CasErrorXC(CasXC):
    """ This is the base class of all CAS-related Errors"""
    pass
    
class ItemNotFoundError(CasErrorXC):
    """ Raised when a content id cannot be located within a CAS """
    
    pass
    
class ItemCorruptedError(CasErrorXC):
    """ Raised when a CAS finds content that does not correspond to the
    content id (i.e. this is a 'checksum error')
    """
    pass
    
