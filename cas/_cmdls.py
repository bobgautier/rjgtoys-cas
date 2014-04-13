#
# sketch of an ls command

import sys
from argparse import ArgumentParser

from _base import CasStore

from _log import getLogger

log = getLogger(__name__)

class ListCommand(object):
    
    def __init__(self):
        pass

    def build_parser(self):
        p = ArgumentParser()

        log.add_options(p)
        self.add_options(p)
        
        return p
        
    def add_options(self,p):

        p.add_argument('cas',metavar='source',type=str,help="Source store")
        
    def parse_args(self,argv):
        p = self.build_parser()
        opts = p.parse_args(argv)
        log.handle_options(opts)
        return opts
        
    def main(self,argv=None):
        
        if argv is None:
            argv = sys.argv[1:]
        
        opts = self.parse_args(argv)
        
        return self.run(opts)

    def run(self,opts):
        
        cas = CasStore(opts.cas,refresh=False)
        
        for i in cas:
            try:
                print i.printable()
            except Exception,e:
                print >>sys.stderr, "Error: %s" % (e)
                print >>sys.stderr, type(i.path)
                print >>sys.stderr, u"Path: %s" % (i.path)
                break
            
if __name__ == "__main__":
    c = ListCommand()
    c.main()
