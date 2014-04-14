
import threading
import time

class ProgressSample(object):
    
    def __init__(self,since,updated,done,steps):
        self.since = since
        self.updated = updated
        self.done = done
        self.steps = steps
    
        self.pcdone = int(done*100/steps)
        t = time.time()
        if self.pcdone:
            self.eta = ((updated-since)*100)/self.pcdone
        else:
            self.eta = t    # Needs to be a time
        
        self.ttg = self.eta - t
        self.elapsed = t-self.since

class ProgressTracker(object):
    
    def __init__(self,steps=100,stop=None):
        self.steps = steps
        self.stop = stop
        self.lock = threading.RLock()
        self.reset()

    def reset(self,done=0):
        with self.lock:
            self.done = done
            self.since = time.time()
            self.updated = self.since

    def update(self,done=1):
        with self.lock:
            self.done += done
            if self.done < 0:
                self.done = 0
            elif self.done > self.steps:
                self.done = self.steps
            self.updated = time.time()
            
    def stop(self):
        if self.stop is None:
            raise Exception("Can't stop this process")
        self.stop()
    
    def sample(self):
        with self.lock:
            s = ProgressSample(
                self.since,
                self.updated,
                self.done,
                self.steps)
        return s

class AlreadyWorkingError(Exception):
    pass

class SlowOperation(object):
    
    def __init__(self):
        self.stopping = threading.Event()
        self._working = threading.Lock()
    
    def work(self,interval,count):
        self.work_start(interval,count)
        return self.work_wait()
    
    def working(self):
        w = False
        
        w = not self._working.acquire(0)
        if not w:
            self._working.release()
        return w

    def work_start(self,interval,count):

        if not self._working.acquire(0):
            raise AlreadyWorkingError()

        self.pt = ProgressTracker(steps=count,stop=self.work_cancel)
        
        self.worker = threading.Thread(target=self.do_work,args=(interval,count))
        self.worker.start()

        return self.pt

    def do_work(self,interval,count):

        try:
            return self._do_work(interval,count)
        finally:
            self._working.release()
            
    def _do_work(self,interval,count):
        for i in range(0,count):
            if self.stopping.is_set():
                return

            time.sleep(interval)
            self.pt.update(1)
            print "worker has done %d" % (i)

    def work_wait(self):

        self.worker.join()

    def work_cancel(self):
        
        self.stopping.set()

s = SlowOperation()


s.work(1,2)


pt = s.work_start(0.7,10)

while True:
    p = pt.sample()
    if p.pcdone == 100:
        break
        
    print "%d/%d in %ds %d%%" % (p.done,p.steps,p.elapsed,p.pcdone)
    time.sleep(0.5)
    print "Working",s.working()
    
s.work_wait()
