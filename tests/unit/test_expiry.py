
from cas._expiry import NEVER, UNKNOWN, EXPIRED, expire_relative, expired

from mock import patch, Mock

def test_ordering():
    assert NEVER > UNKNOWN
    assert NEVER > EXPIRED
    assert UNKNOWN > EXPIRED

def test_relative():
    with patch('time.time',Mock(return_value=0)):
        assert expire_relative(seconds=1) == 1
        assert expire_relative(minutes=1) == 60
        assert expire_relative(hours=1) == 3600
        assert expire_relative(days=1) == 3600*24
        
        assert expire_relative(seconds=1,minutes=1,hours=1,days=1) == (3600*24)+3600+60+1

def test_never():
    assert not expired(NEVER)
    
def test_unknown():
    assert not expired(UNKNOWN)
    
def test_expired():
    assert expired(EXPIRED)
    
    
