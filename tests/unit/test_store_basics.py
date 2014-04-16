#
# Basic tests on stores
#

from rjgtoys.cas._base import CasStoreVolatile
from rjgtoys.cas._expiry import NEVER

def test_store_short():
    
    s = CasStoreVolatile()
    
    cid = s.store('one',expiry=NEVER)

    assert cid in s
    
    assert s.fetch(cid) == 'one'
    
