#
# sketch of a refresh command

import sys
from argparse import ArgumentParser

from _base import CasStore

import cas

from rjgtoys import logs

log = logs.getLogger(__name__)

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
        p.add_argument('-f','--force',dest='force',help="Force a full scan",action="store_true",default=False)
        p.add_argument('-c','--checkpoint',dest='cp',help="Checkpoint data periodically (seconds)",default=0,action="store",type=int)
        
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
        
        if opts.dryrun:
            opts.cp = 0
        
        log.info("Checkpoint interval %d" % (opts.cp))
        
        cas.refresh(force=opts.force,checkpoint=opts.cp)
        if not opts.dryrun:
            log.verbose("Saving changes")
            cas.save()
            log.info("Store has been updated.")
        else:
            log.info("DRYRUN: no changes made")
            
if __name__ == "__main__":
    c = RefreshCommand()
    c.main()
