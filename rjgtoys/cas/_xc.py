#
# exceptions associated with cas
#

import xc

class CasXC(xc.BaseXC):
    pass
    
class CasErrorXC(CasXC):
    pass
    
class ItemNotFoundError(CasErrorXC):
    pass
    
class ItemCorruptedError(CasErrorXC):
    pass
    
