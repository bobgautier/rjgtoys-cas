#
# sketch of a refresh command

import sys
from argparse import ArgumentParser

from _base import CasStore

from _log import getLogger

log = getLogger(__name__)

class RefreshCommand(object):
    
    def __init__(self):
        pass

    def build_parser(self):
        p = ArgumentParser()

        log.add_options(p)
        self.add_options(p)
        
        return p
        
    def add_options(self,p):

        p.add_argument('-n','--dryrun',dest='dryrun',help="Dry run: don't write anything back",action="store_true",default=False)
        
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
        
        cas = CasStore(opts.cas)
        
        cas.refresh()
        if not opts.dryrun:
            log.verbose("Saving changes")
            cas.save()
            log.info("Store has been updated.")
        else:
            log.info("DRYRUN: no changes made")
            
if __name__ == "__main__":
    c = RefreshCommand()
    c.main()
