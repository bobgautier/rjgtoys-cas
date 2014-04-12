#
# Fixtures for testing cas
#

import os
from mock import patch

def stat_result(mode=None,ino=None,dev=None,uid=None,gid=None,
            size=None,atime=None,mtime=None,ctime=None):
    return os.stat_result((mode,ino,dev,0,uid,gid,size,atime,mtime,ctime))

#
# Stuff for messing with the clock and passage of time
#

import time

def epochtime(s):

    if s is None or s == 'now':
        return time.time()
    
    try:
        s = float(s)
        return s
    except:
        pass

    if not isinstance(s,basestring):
        raise TypeError("Could not convert '%s' to epoch time" % (s))

    for f in ('%Y-%m-%d %H:%M:%S','%Y-%m-%d %H:%M', '%Y-%m-%d',
                '%H:%M:%S','%H:%M'):
        try:
            t = time.strptime(s,f)
            if not f.startswith('%Y'):
                t0 = time.localtime()
                t = time.struct_time((t0.tm_year,t0.tm_mon,t0.tm_mday,t.tm_hour,t.tm_min,t.tm_sec,t0.tm_wday,t0.tm_yday,t0.tm_isdst))

            t = time.mktime(t)
            print "DEBUG: epochtime %s is %s" % (s,epochstr(t))
            return t
        except:
            pass
            
    raise TypeError("Could not convert '%s' to an epoch time" % (s))

def epochstr(t):
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(t))

class MockClock(object):
    def __init__(self,start=None,rate=1.0):
        self._clock = epochtime(start)
        self._rate = rate

    def time(self):
        t = self._clock
        self._clock += self._rate
        return t
        
    def wait(self,t):
        self._clock += t

    @property
    def rate(self):
        return self._rate
        
    @rate.setter
    def rate(self,rate):
        self._rate = rate

    @property
    def clock(self):
        return self._clock

    @clock.setter
    def clock(self,t):
        self._clock = epochtime(t)
