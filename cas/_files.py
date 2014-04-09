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
from gzip import GzipFile

from _base import CasStoreBase, cas_link_to_id, cas_file_to_id, cas_to_json, cas_from_json

import cas

log = cas.log.getLogger(__name__)

# Default relative path to metadata file

DEFAULT_METADATA='.cas'

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
    
    version="1"
    
    def __init__(self,path=None,dir='',state=None):
        
        if state is not None:
            return self.__setstate__(state)

        self.expiry = None
        self.path = path
        self.dir = dir
        self.clear()
        self.refresh()

        self.__dict__['version'] = self.version
        
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

    def __getstate__(self):
        return self.__dict__
        
    def __setstate__(self,state):
        assert state.version == self.version
        self.__dict__.update(state)
        
class CasFileTreeStore(CasStoreBase):

    version="1"
    
    def __init__(self,content=None,metadata=None,refresh=None):
        self.content = os.path.normpath(content)+'/'
        self.metadata = metadata
        
        self.byid = {}
        self.bypath = {}

        # If we got content but no metadata,
        # force a refresh by default
        
        if not self.load() and refresh is None:
            refresh = True
            
        if refresh:
            self.refresh()
    
    def load(self,metadata=None):
        if self.content is None:
            return True

        if metadata is not None:
            self.metadata = metadata
        
        if self.metadata is None:
            self.metadata = DEFAULT_METADATA
            
        path = os.path.join(self.content,self.metadata)
        log.debug("Loading from %s" % (path))
        
        try:
            with GzipFile(path) as f:
                self.__setstate__(cas_from_json(f.read()))
            return True
        except Exception,e:
            if isinstance(e,IOError) and e.errno == 2:  # Not found
                log.debug("(No metadata found at %s)" % (path))
                return False
            log.debug("Failed to load metadata %s:%s" % (path,e))

        return False
        
    def save(self,metadata=None):
        if self.content is None:
            return False

        if metadata is not None:
            self.metadata = metadata
            
        if self.metadata is None:
            self.metadata = DEFAULT_METADATA
        
        path = os.path.join(self.content,self.metadata)
        
        try:
            with GzipFile(path,'wb') as f:
                f.write(cas_to_json(self))
            log.debug("Saved state to %s" % (path))
            return True
        except Exception,e:
            log.warning("Failed to save metadata %s: %s" % (path,e))
        
        return False
        
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
                if i.refresh():
                    log.debug("Metadata for %s was out of date" % (path))
                else:
                    log.debug("Assuming metadata current for %s" % (path))
            except Exception,e:
                log.debug("refresh: for path '%s': %s" % (path,e))
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
                log.debug("Found new item at %s" % (p))
                i = CasFSItem(path=p,dir=self.content)
                self.byid[i.cid] = i
                self.bypath[i.path] = i
            except Exception,e:
                log.error("Create Item failed for '%s': %s" % (p,e))
                pass
        
    def _paths(self):
        """
        Return all the content-root relative paths of
        objects in the content-root.
        """

        suffix=len(self.content)
        for (d,k,fs) in os.walk(self.content):
#            print "dir %s" % (d)

            yield d[suffix:]
            for f in fs:
                p = os.path.join(d,f)[suffix:]
#                print " file %s" % (p)
                yield p
                
    def _fetch(self,item):
        """ Fetch content of an item and ensure that it
        matches the id we expect.  If not, update for the
        new id, but return nothing from this fetch """
        
        pass

    def __getstate__(self):
        return dict(version=self.version,item=self.bypath.values())
    
    def __setstate__(self,state):
        assert state.version == self.version

        self.byid = {}
        self.bypath = {}
        self.content = None
        self.metadata = None
        
        for i in state.item:
            ci = CasFSItem(state=i)
            self.byid[ci.cid] = ci
            self.bypath[ci.path] = ci
