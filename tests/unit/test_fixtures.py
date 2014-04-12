#
# test the fixtures
#
# Should one test fixtures?   It's nice to know they work, but it's
# likely that if they don't some other tests will fail.
#
# So maybe the tests are redundant, but I suspect it would be possible
# to create a broken fixture that would allow tests to pass that shouldn't.
#
# It's nice to see coverage reports for fixtures too, although the tests
# that use the fixtures should cover 100% of the fixture code, otherwise
# you've got redundant fixture code.
#
# Anyway, here are the tests...
#

import time

from fixtures import stat_result, epochtime, epochstr, MockClock

import pytest
from mock import patch

def echeck(fmt,spec,result=None):
    t0 = time.strptime(spec,fmt)
    
    t = epochtime(spec)
    t1 = time.localtime(t)
    
    assert (t1.tm_hour,t1.tm_min,t1.tm_sec) == (t0.tm_hour,t0.tm_min,t0.tm_sec)
    
    if spec.startswith('%Y'):
        assert (t1.tm_year,t1.tm_mon,t1.tm_mday,t1.tm_wday,t1.tm_yday,t1.tm_isdst) == (t0.tm_year,t0.tm_mon,t0.tm_mday,t1.tm_wday,t1.tm_yday,t1.tm_isdst)
        
    if result is None:
        result = spec
        
    assert epochstr(t) == result

def test_epochtime():

    # wait until we've got a second
    
    while True:
        t0 = time.time()
        t1 = int(t0)
        if (t0-float(t1)) < .1:
            break
        time.sleep(.1)
        print "Wait..."

    n0 = epochtime(None)
    n1 = epochtime('now')
    
    assert int(n0) == t1
    assert int(n1) == t1
    
    n2 = epochtime(n1+1)
    
    assert n2 == n1+1
    
    echeck('%Y-%m-%d %H:%M:%S','2009-10-03 14:10:56')
    echeck('%Y-%m-%d %H:%M','2004-06-02 09:02','2004-06-02 09:02:00')
    echeck('%Y-%m-%d','2010-01-03','2010-01-03 00:00:00')
    
    date = epochstr(epochtime('now'))[:11]
    
    echeck('%H:%M:%S','10:02:00',date+'10:02:00')
    echeck('%H:%M','23:12',date+'23:12:00')
    
    with pytest.raises(TypeError):
        epochtime('2001/02/03')
    with pytest.raises(TypeError):
        epochtime('yesterday')

    with pytest.raises(TypeError):
        epochtime(('No','tuples'))

def test_stat_result():
    
    s = stat_result(mode=0100755,ino=42,dev=12,uid=500,gid=12,size=1002,atime=101,mtime=102,ctime=103)
    
    assert s.st_mode  == 0100755
    assert s.st_ino   == 42
    assert s.st_dev   == 12
    assert s.st_uid   == 500
    assert s.st_gid   == 12
    assert s.st_size  == 1002
    assert s.st_atime == 101
    assert s.st_mtime == 102
    assert s.st_ctime == 103

def test_mock_clock():
    
    now = time.time()
    
    c = MockClock(start=now)
    
    assert c.clock == now
    assert c.rate == 1.0
    
    assert c.time() == now
    assert c.time() == now+1.0

    c.wait(8.0)
    
    assert c.time() == now + 10.0
    
    c.clock = now
    c.rate = 2.0
    
    assert c.time() == now
    assert c.time() == now + 2.0
    
def test_mock_clock_usecase():
    
    now = epochtime('2014-03-02')
    
    mc = MockClock('2014-03-02')
    
    assert mc.clock == now
    
    with patch('time.time',mc.time):
        
        assert time.time() == now
        
        assert time.time() == now + 1.0
        
        mc.wait(2)
        
        assert time.time() == now + 4.0
        

    
