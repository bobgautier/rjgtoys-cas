import time
from cas._tracker import ProgressTracker

def do_work(pt,interval,count):
    pt.set_goal(count)
    for i in range(0,count):
        if pt.stopping():
            return

        time.sleep(interval)
        pt.update(1)
#        print "worker has done %d" % (i)


s = ProgressTracker(target=do_work)


s(1,2)

s.start(1,20)

while True:
    s.sample()
    eta = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(s.eta))
    print "%d/%d in %ds %d%% %s %d" % (s.done,s.steps,s.elapsed,s.pcdone,eta,s.ttg)
    if s.pcdone == 100:
        break
    time.sleep(0.5)
#    print "Working",s.started()
    
s.wait()
