import sys
import time

def readfile(p):
    with open(p) as f:
        d = f.read()
    print "Read %d bytes from %s" % (len(d),p)
    
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
    
