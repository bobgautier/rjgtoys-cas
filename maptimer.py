import sys
import time
import mmap
from hashlib import sha512

def readfile(p):
    with open(p) as f:
        d = mmap.mmap(f.fileno(),0,mmap.MAP_SHARED,mmap.PROT_READ)
    print "Read %d bytes from %s" % (len(d),p)

    i = 0
    s = 0
    while i < len(d):
        s += ord(d[i])
        i+=4096
        
def test(p):
    t0 = time.time()
    readfile(p)
    t1 = time.time()
    readfile(p)
    t2 = time.time()
    
    r1 = t1-t0
    r2 = t2-t1
    
    
    print "First time took %fs, second took %fs (%2d%%)\n" % (r1,r2,int(r2*100/r1))
    
for p in sys.argv[1:]:
    test(p)
    
