#
# file tree cas
#

import sys
import os
import stat
import json
import pwd
import grp
import stat
import time

from _base import CasStoreBase, cas_link_to_id, cas_file_to_id


OTYPE_FILE = 'F'
OTYPE_DIR = 'D'
OTYPE_LINK = 'L'
OTYPE_FIFO = 'P'
OTYPE_SOCK = 'S'
OTYPE_CHR = 'C'
OTYPE_BLK = 'B'

stat_to_otype = {
    stat.S_IFSOCK: OTYPE_SOCK,
    stat.S_IFLNK: OTYPE_LINK,
    stat.S_IFREG: OTYPE_FILE,
    stat.S_IFBLK: OTYPE_BLK,
    stat.S_IFDIR: OTYPE_DIR,
    stat.S_IFCHR: OTYPE_CHR,
    stat.S_IFIFO: OTYPE_FIFO,
}

# http://code.activestate.com/recipes/578231-probably-the-fastest-memoization-decorator-in-the-/

def memodict(f):
    """ Memoization decorator for a function taking a single argument """
    class memodict(dict):
        def __missing__(self, key):
            ret = self[key] = f(key)
            return ret 
    return memodict().__getitem__

@memodict
def getuserbyid(uid):
    try:
        return pwd.getpwuid(uid).pw_name
    except:
        return None

@memodict        
def getgroupbyid(gid):
    try:
        return grp.getgrgid(gid).gr_name
    except:
        return None



class CasFSItem(object):
    """
    A filesystem item: the object contains all you need to know
    to be able to recreate the object, except the (file or link)
    content.
    """
    
    json_version="1.0"
    
    def __init__(self,path=None,dir=''):
        
        self.expiry = None
        self.path = path
        self.dir = dir
        self.clear()
        self.refresh()

        self.__dict__['json_version'] = self.json_version
        
    def refresh(self,path=None,dir=''):
        """
        Update the info held here if necessary and
        return True if anything was changed
        """

        if path is not None:
            self.clear()
            self.path = path
            self.dir = dir
            
        if self.path is None:
            return False
        
        path = os.path.join(self.dir,self.path)
        try:
            s = os.lstat(path)
        except:
            self.clear()
            return True

        # mtime look ok?
        
        if self.mtime is not None and self.mtime == s.st_mtime:
            return False

        while True:
            # update everything
            
            self.stime = time.time()
            
            self.mode = stat.S_IMODE(s.st_mode)
            self.uid = s.st_uid
            self.gid = s.st_gid
            self.size = s.st_size
            self.atime = s.st_atime
            self.mtime = s.st_mtime
            self.ctime = s.st_ctime
            
            self.otype = stat_to_otype.get(stat.S_IFMT(s.st_mode),None)
    
            self.uname = getuserbyid(self.uid)
            self.gname = getgroupbyid(self.gid)
    
            # Try to compute the cid
            
            if self.otype == OTYPE_FILE:
                self.cid = cas_file_to_id(path,self.size)
            elif self.otype == OTYPE_LINK:
                self.cid = cas_link_to_id(path,self.size)
            else:
                self.cid = None
    
            # verify the mtime following collection of the content
    
            s1 = os.lstat(path)
    
            if (s1.st_mode == s.st_mode) and (s1.st_mtime == s.st_mtime):
                # we are still current
                break
        
            s = s1  # prepare to go around again

        return True
        
    def clear(self):
        self.mode = None
        self.uid = None
        self.gid = None
        self.size = None
        self.atime = None
        self.mtime = None
        self.ctime = None
        self.otype = None
        # Cas-specifics
        self.cid = None
        self.uname = None
        self.gname = None

    @property
    def expired(self):
        return expired(self.expiry)

    def get_json(self):
        return self.__dict__
        
class CasFileTreeStore(CasStoreBase):

    json_version="1.0"
    
    def __init__(self,content=None,metadata=None,scan=False):
        self.content = os.path.normpath(content)+'/'
        self.metadata = metadata
        
        self.byid = {}
        self.bypath = {}
        
        self.refresh()

        self.__dict__['json_version'] = self.json_version
        
    def __iter__(self):
        return self.bypath.itervalues()

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
        
        if item.expired:
            del self.item[ci]
            raise ItemNotFoundError()

        return self._fetch(item)

    def refresh(self):
        
        expectpaths = set(i.path for i in self.bypath.values())

        allpaths = set(self._paths())
        
        newpaths = allpaths - expectpaths
    
        for i in self.bypath.itervalues():
            cid = i.cid
            path = i.path
            try:
                i.refresh()
            except:
                try:
                    del self.byid[cid]
                except:
                    pass
                try:
                    del self.bypath[path]
                except:
                    pass

        for p in newpaths:
            try:
                i = CasFSItem(path=p,dir=self.content)
                self.byid[i.cid] = i
                self.bypath[i.path] = i
            except:
                pass
        
    def _paths(self):
        """
        Return all the content-root relative paths of
        objects in the content-root.
        """

        suffix=len(self.content)
        for (d,k,fs) in os.walk(self.content):
            print "dir %s" % (d)

            yield d[suffix:]
            for f in fs:
                p = os.path.join(d,f)[suffix:]
                print " file %s" % (p)
                yield p
                
    def _fetch(self,item):
        """ Fetch content of an item and ensure that it
        matches the id we expect.  If not, update for the
        new id, but return nothing from this fetch """
        
        pass

    def get_json(self):
        return dict(json_version=self.json_version,items=self.bypath.values())
        
