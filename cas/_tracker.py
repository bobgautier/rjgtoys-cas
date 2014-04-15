
import threading
import time

class NothingToDoError(Exception):
    pass

class AlreadyStartedError(Exception):
    pass

class ActionFailedError(Exception):
    pass

class ProgressTracker(object):

    def __init__(self,target=None,name=None):
        self._target = target
        self.name = name
        self._lock = threading.RLock()
        self._stopping = threading.Event()
        self._started = threading.Event()
        self._running = False
        
        self._steps = 0
        self._done = 0

    def run(self,*args,**kwargs):
        """
        Call the action of this tracker.   The current
        tracker is always passed as the first parameter
        
        May be overridden in a subclass.
        """

        if self._target is None:
            raise NothingToDoError(self)

        return self._target(self,*args,**kwargs)

    def _run_stop(self,*args,**kwargs):
    
        result = self.run(*args,**kwargs)

        if not self._started.is_set():  # Failed to call set_goal?
            return                      # caller will notice and raise ActionFailedException

        with self._lock:
            self.update(0)      # Ensure final update
            self._started.clear()
            self._running = False
            
        return result

    def start(self,*args,**kwargs):
        """
        Start the action.  Needs to reset the progress info too.
        """
        
        with self._lock:
            
            if self._running:
                raise AlreadyStartedError(self)

            self._running = True
            self._started.clear()

            self.since = time.time()
            try:
                self._worker = threading.Thread(target=self._run_stop,name=self.name,args=args,kwargs=kwargs)
                self._worker.start()
            except:
                self._running = False
                raise

            while not self._started.wait(1.0):      # Wait for operation to start
                if not self._worker.is_alive():     # keeping an eye on early abort
                    self._running = False           # Not running after all
                    raise ActionFailedError(self)
    
    def started(self):
        return self._started.is_set()

    def stop(self):
        self._stopping.set()

    def stopping(self):
        return self._stopping.is_set()

    def set_goal(self,steps=None,done=0):
        """
        Called from run: sets the goal of
        this action (defined by a number of steps)
        
        Until this is done nothing will see any progress
        reports and the action is not considered
        'started'
        
        *MUST* be called by the action.
        
        The main lock is already held.
        """

        if steps is not None:
            self._steps = steps
        self._done = done
        self._updated = time.time()
        
        self._started.set()
    
    def update(self,done=1):
        """
        Called by the action whenever it has made
        some progress
        """

        with self._lock:
            t = time.time()
            
            self._updated = t
            
            self._done += done
            
            if self._done < 0:
                self._done = 0
            elif self._done > self._steps:
                self._done = self._steps
        
    def stop(self):
        self._stopping.set()

    def sample(self):
        with self._lock:
            
            t = time.time()
            
            self.sampled = t
            
            self.updated = self._updated
            self.steps = self._steps
            self.done = self._done
            
            if self.steps:
                self.pcdone = int(self.done*100/self.steps)
            else:
                self.pcdone = 0

            if self.pcdone:
                # time to go = time to do the rest - time since the update
                self.ttg = (((self.updated-self.since)*(100.-self.pcdone))/self.pcdone)-(self.sampled-self.updated)
            else:
                self.ttg = 60.0    # Needs to be a time
        
            self.eta = self.ttg + t
            self.elapsed = t-self.since

    def wait(self,timeout=None):

        self._worker.join(timeout)

    def __call__(self,*args,**kwargs):
        """
        A simple synchronous call
        """

        self.start(*args,**kwargs)
        self.wait()
        # No result?
