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
        
        self.item = {}

        self.refresh()


    def store(self,s,expiry=None,size=None,cid=None):
        """
        Store the stream s with expiry specified
        
        Return the contentitem
        
        Limit the size if size is not None
        
        If the cid is given, check that the stream content
        matches, and if not fail with ItemCorruptError
        """
        
        raise CasReadOnlyError()
        
    def fetch(self,ci):
        
        ci = CasId(ci)
        item = self.item[ci]
        
        if expired(item.expiry):
            del self.item[ci]
            raise ItemNotFoundError()

        return self._fetch(item)

    def refresh(self):
        
        expectids = set(self.item.keys())
        expectpaths = set(i.path for i in self.item.values())

        allpaths = set(self._paths())
        
        newpaths = allpaths - expectpaths
    
        for cid,i in self.item.iteritems():
            try:
                i.refresh()
            except:
                del self.item[cid]
        
        for p in newpaths:
            try:
                i = CasStat(p)
                self.item[i.cid] = i
            except:
                pass
        
    def _paths(self):

        for (d,k,fs) in os.walk(self.content):
            print "dir %s" % (d)

            for f in fs:
                p = os.path.join(d,f)

                yield p
                
    def _fetch(self,item):
        """ Fetch content of an item and ensure that it
        matches the id we expect.  If not, update for the
        new id, but return nothing from this fetch """
        
        pass
        
if __name__ == "__main__":
    
    for r in sys.argv[1:]:
        
        f = FileTreeStore(r)
        f.scan()
