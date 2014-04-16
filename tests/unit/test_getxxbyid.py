#
# Test the file stat function
#
# Because it messes with memoised functions this could have
# nasty side-effects on later tests.
#

from rjgtoys.cas._files import getuserbyid, getgroupbyid
from mock import Mock, patch
import pytest
import pwd
import grp

uids = {
    1: 'uone',
    2: 'utwo',
    3: 'uthree'
}

gids = {
    10: 'gone',
    20: 'gtwo',
    30: 'gthree'
}

def mock_getpwuid(uid):
    return pwd.struct_pwent((uids[uid],'pwd',uid,uid,'gecos','dir','sh'))

def mock_getgrgid(gid):
    return grp.struct_group((gids[gid],'pwd',gid,[]))
    
def test_getuserbyid_memoise():
    m = Mock(wraps=mock_getpwuid)
    with patch('pwd.getpwuid',m):
        assert getuserbyid(1) == 'uone'
        assert getuserbyid(1) == 'uone'
    assert len(m.call_args_list) == 1
    
def test_getgroupbyid_memoise():
    m = Mock(wraps=mock_getgrgid)
    with patch('grp.getgrgid',m):
        assert getgroupbyid(10) == 'gone'
        assert getgroupbyid(10) == 'gone'
    assert len(m.call_args_list) == 1

def test_getuserbyid_neg_memoise():
    m = Mock(wraps=mock_getpwuid)
    with patch('pwd.getpwuid',m):
        assert getuserbyid(100) is None
        assert getuserbyid(100) is None
    assert len(m.call_args_list) == 1
    
def test_getgroupbyid_neg_memoise():
    m = Mock(wraps=mock_getgrgid)
    with patch('grp.getgrgid',m):
        assert getgroupbyid(100) is None
        assert getgroupbyid(100) is None
    assert len(m.call_args_list) == 1

def test_getuserbyid():
    m = Mock(wraps=mock_getpwuid)
    with patch('pwd.getpwuid',m):
        for uid,uname in uids.items():
            assert getuserbyid(uid) == uname
            
def test_getgroupbyid():
    m = Mock(wraps=mock_getgrgid)
    with patch('grp.getgrgid',m):
        for gid,gname in gids.items():
            assert getgroupbyid(gid) == gname

            
