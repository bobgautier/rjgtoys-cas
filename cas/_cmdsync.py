#
# sketch of the sync command

import sys
from argparse import ArgumentParser

from _base import CasOpen
    
class SyncCommand(object):
    
    def __init__(self):
        pass

    def build_parser(self):
        p = ArgumentParser()
        
        self.add_options(p)
        
        return p
        
    def add_options(self,p):
        p.add_argument('-v','--verbose',dest='verbose',help="Enable verbose output",action="store_true",default=False)
        p.add_argument('src',metavar='source',type=str,help="Source store")
        p.add_argument('dst',metavar='dest',type=str,help="Destination store")
        
    def parse_args(self,argv):
        p = self.build_parser()
        opts = p.parse_args(argv)
        return opts
        
    def main(self,argv=None):
        
        if argv is None:
            argv = sys.argv[1:]
        
        opts = self.parse_args(argv)
        
        return self.run(opts)

    def run(self,opts):
        
        src = CasOpen(opts.src)
        dst = CasOpen(opts.dst)
        
        for ci in src:
            if ci not in dst:
                f = src.get(ci)
                dst.put(f,ci)
        
        if not opts.delete:
            return
            
        # do deletes
        
        for ci in dst:
            if not ci in src:
                dst.delete(ci)
                
if __name__ == "__main__":
    c = SyncCommand()
    c.main()
    
