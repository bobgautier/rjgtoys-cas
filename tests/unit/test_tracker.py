import time
from rjgtoys.cas._tracker import ProgressTracker, ActionFailedError

import threading
import pytest
import Queue

def triv(pt):
    pt.set_goal(1)


triv = ProgressTracker(target=triv)
    # FIXME: needs to be a decorator
    
def test_triv():

    triv()

def startfails(pt,raiseit):
    if raiseit:
        raise Exception("failure in action")
        
    return  # Fails to call set_goal

startfails = ProgressTracker(target=startfails)

def test_startfails_return():
    
    with pytest.raises(ActionFailedError):
        startfails.start(False)
        
def test_startfails_exception():
    with pytest.raises(ActionFailedError):
        startfails.start(True)

@ProgressTracker
def decorated(pt,q):
    g = q.get()
    q.task_done()
    
    pt.set_goal(g)
    
    n = 0
    while n < g:
        i = q.get()
        n += 1
        pt.update(1)
        q.task_done()
        
def test_decorated():
    q = Queue.Queue()
    q.put(2)
    
    decorated.start(q)
    
    q.join()        # wait for step count to be consumed
    
    for _ in range(0,2):
        q.put(1)    # step the thread
        q.join()    # wait for it to be done

        decorated.sample()  # sample progress
        
        

def stepper(pt,steps,cond,signal):
    pt.set_goal(steps)
    cond.acquire()
    signal.acquire()
    done = 0
    while done < steps:
        signal.acquire()
        cond.wait()
        done += 1
        print "stepper done %d" % (done)
        pt.update(1)
        signal.notify()
        signal.release()
        
stepper = ProgressTracker(target=stepper)

def xtest_stepper():
    
    control = threading.Condition()
    signal = threading.Condition()
    
    control.acquire()
    signal.acquire()
    
    s = stepper.start(5,control,signal)
    
    assert s.started()
    
    for i in range(1,4):
        control.acquire()
        control.notify()
        control.release()
        
        signal.wait()
        signal.release()
        s.sample()
