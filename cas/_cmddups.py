#
# a command to list those items that
# appear more than once
#

import sys
from argparse import ArgumentParser

from _base import CasStore

from _log import getLogger

log = getLogger(__name__)

class DupsCommand(object):
    
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
        
        seen = {}
        
        
        
        for i in cas:
            if i.cid is None:
                continue

            try:
                seen[i.cid].append(i.path)
            except:
                seen[i.cid] = [i.path]

        for i,ps in seen.iteritems():
            if len(ps) == 1:
                continue

            print i
            for p in sorted(ps):
                print "  ",p

if __name__ == "__main__":
    c = DupsCommand()
    c.main()
