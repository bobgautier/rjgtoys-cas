#
# file tree cas
#

import sys
import os
import stat

from hashlib import sha512
from base64 import b64encode

from _base import ContentItem,Store

class FileTreeItem(ContentItem):

    def __init__(self,cid,size,expiry,path):
        self.cid = cid
        self.size = size
        self.expiry = expiry
        self.path = path
        
class FileTreeStore(Store):

    def __init__(self,content=None,metadata=None,scan=False):
        self.content = content
        self.metadata = metadata
        
        self.idmap = {}
        
    def get(self,ci):
        pass

    def put(self,s,expiry=None,size=None,cid=None):
        """
        Store the stream s with expiry specified
        
        Return the contentitem
        
        Limit the size if size is not None
        
        If the cid is given, check that the stream content
        matches, and if not fail with ItemCorruptError
        """
        
        pass

    def verify(self):
        
        expectids = set(self.idmap.keys())
        actual = self._rescan()
        
        actualids = set(actual.keys())
        
        deleted = expectids - actualids
        
        added = actualids - expectids
        
        self.idmap = actual
        return (deleted,added)


    def scan(self):
        self.idmap = self._rescan()
        
    def _rescan(self):
        
        result = {}
        for (d,k,fs) in os.walk(self.content):
            print "dir %s" % (d)

            for f in fs:
                p = os.path.join(d,f)
                if not os.path.isfile(p): continue
                print "  %s" % (f)
                s = os.stat(p)
                fmt = int(s[stat.ST_MTIME])
                size = s[stat.ST_SIZE]

                cid = getcid(p)

                print cid,size,p

                result[cid] = FileTreeItem(cid,size,None,f)

        return result

if __name__ == "__main__":
    
    for r in sys.argv[1:]:
        
        f = FileTreeStore(r)
        f.scan()
