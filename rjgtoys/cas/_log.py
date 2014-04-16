#
# Logging with some UI support
#
# Should one day be moved out of here and
# re-exported from cas.
#

import sys
import logging

_debug = False
_verbose = False

def configure():
    logging.basicConfig(stream=sys.stdout,level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")

def set_verbose(verbose=None):
    global _verbose
    
    #print "set_verbose: prev %s new %s" % (_verbose,verbose)
    v = _verbose
    if verbose is not None:
        _verbose = verbose
    return v
    
def set_debug(debug=None):
    global _debug

    #print "set_debug: prev %s new %s" % (_debug,debug)
    d = _debug
    if debug is not None:
        _debug = debug
    return d

# FIXME: define a VERBOSE priority level

class MyAdapter(logging.LoggerAdapter):

    def verbose(self,msg):
        #print "VERBOSE: %s" % (msg)
        global _verbose
        if _verbose:
            self.info(msg)
            
    def debug(self,msg):
        global _debug
        if _debug:
            super(MyAdapter,self).debug(msg)

    def add_options(self,p):
        p.add_argument("--debug",help="Enable debug",
            dest="_logdebug", action="store_true", default=None)
            
        p.add_argument("--verbose",help="Verbose output",
            dest="_logverbose", action="store_true", default=None)

        return p
    
    def handle_options(self,opts):
        
        self.set_verbose(opts._logverbose)
        self.set_debug(opts._logdebug)
        
    def set_verbose(self,verbose=None):
        return set_verbose(verbose)
    
    def set_debug(self,debug=None):
        return set_debug(debug)


def getLogger(name):
    if name == "__main__":
        configure()
    return MyAdapter(logging.getLogger(name),{})
