
from cas._expiry import NEVER, UNKNOWN, EXPIRED, expire_relative, expired, expiry, InvalidExpiryError

from mock import patch, Mock
import pytest

import time

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
    
def test_expiry():
    
    t = time.mktime(time.strptime("2008-03-19 19:00","%Y-%m-%d %H:%M"))
    
    with patch('time.time',Mock(return_value=t)):
        assert not expired(expiry("2010-01-01"))
        assert expired(expiry("2001-01-01"))
        
def test_bad_expiry():
    
    for e in (-1,'2010-02-31','02/03/1999','23:70'):
        with pytest.raises(InvalidExpiryError):
            e = expiry(e)
        
def test_valid_expiry():
    
    for e in (14,'2014-02-03','2014-03-19T20:10'):
        assert expiry(e) > 0

