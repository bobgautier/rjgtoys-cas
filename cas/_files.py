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

def statdir(d):
    """ Generate a sequence of (path,stat) pairs
    for all entries in a directory and below
    """
    d = os.path.normpath(d)
    q = [d]
    
    suffix = len(d)+1
    
    while q:
        d = q.pop()

        try:
            e = os.listdir(d)
        except Exception,e:
            log.error("Failed to list directory %s: %s" % (d,e))
            continue
            # FIXME: stat again in case it's changed?
        
        for f in e:
            p = os.path.join(d,f)
            
            try:
                s = os.lstat(p)
            except Exception,e:
                log.error("Failed to stat %s: %s" % (p,e))
                continue

            yield (p[suffix:],s)
            
            if stat.S_ISDIR(s.st_mode):
                q.append(p)


kB=1024
MB=kB*1024
GB=MB*1024
TB=GB*1024
PB=TB*1024

def sizestr(s,unit='B'):
    s = float(s)
    for (threshold,suffix) in ((PB,'P'),(TB,'T'),(GB,'G'),(MB,'M'),(kB,'k')):
        if s >= threshold:
            return "%6.1f%s%s" % (s/threshold,suffix,unit)
    return "%.1f%s" % (s,unit)


class CasFSItem(object):
    """
    A filesystem item: the object contains all you need to know
    to be able to recreate the object, except the (file or link)
    content.
    """
    
    version="1"
    
    def __init__(self,path=None,stat=None,saved=None):

        if saved is not None:
            return self.__setstate__(saved)

        self.__dict__['version'] = self.version
        
        self.expiry = None
        self.path = path
        self.clear()
        if path is not None and stat is not None:
            self.update(path,stat)

    def update(self,path,s):
        """
        Update the info held here if necessary and
        return True if the content id is likely to have changed
        """

        self.path = path
        
        self.stale = False
        if self.mtime is None or self.mtime != s.st_mtime:
            self.mtime = s.st_mtime
            self.stale = True
        
        fileid = (s.st_dev,s.st_ino)
        if self.fileid is None or self.fileid != fileid:
            self.fileid = fileid
            self.stale = True
        
        self.stime = time.time()
            
        self.mode = stat.S_IMODE(s.st_mode)
        if self.uid != s.st_uid:
            self.uid = s.st_uid
            self.uname = getuserbyid(self.uid)

        if self.gid != s.st_gid:
            self.gid = s.st_gid
            self.gname = getgroupbyid(self.gid)

        self.size = s.st_size
        self.atime = s.st_atime
        self.mtime = s.st_mtime
        self.ctime = s.st_ctime
            
        self.otype = stat_to_otype.get(stat.S_IFMT(s.st_mode),None)

        return self.stale

    def refresh(self,d=None):
    
        assert self.stale
    
        if d is None:
            d = ''

        tries = 0
        while self.stale:
            tries += 1
            
        # Try to compute the cid

            path = os.path.join(d,self.path)

            if self.otype == OTYPE_FILE:
                self.cid = cas_file_to_id(path,self.size)
            elif self.otype == OTYPE_LINK:
                self.cid = cas_link_to_id(path,self.size)
            else:
                self.cid = None
        
            try:
                s = os.lstat(path)
            except Exception,e:
                log.error("Failed to stat %s: %s" % (path,e))
                self.clear()
                return self
                
            self.update(self.path,s)
            if self.stale:
                if tries > 3:
                    log.error("File %s is changing too often - giving up" % (path))
                    self.clear()
                    return self
                    
                log.warning("File %s changed during reading - retrying" % (path))

        return self

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
        self.fileid = None
        self.cid = None
        self.uname = None
        self.gname = None
        self.stale = False
        self.stime = 0

    @property
    def expired(self):
        return expired(self.expiry)

    def __getstate__(self):
        return self.__dict__
        
    def __setstate__(self,state):
        assert state.version == self.version
        self.__dict__.update(state)
        self.fileid = tuple(self.fileid) # JSON will represent this as a list
        #
        # Paths will have started off as ordinary strings, but JSON will
        # have made them unicode; we can safely convert back (I claim)
        #
        if self.path is not None:
            self.path = str(self.path)
class CasFileTreeStore(CasStoreBase):

    version="1"
    
    def __init__(self,content=None,metadata=None,refresh=None):
        self.content = os.path.normpath(content)
        self.metadata = metadata
        
        self.byfileid = {}  # Locate each by device and inode
        self.bypath = {}    # Locate by file path
        self.byid = {}      # Locate by content id

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
        
        newentries = 0
        newbytes = 0
        
        origentries = 0
        origbytes = 0

        find_time = time.time()
        
        for (p,s) in statdir(self.content):
            log.debug("refresh found %s" % (p))
            fileid = (s.st_dev,s.st_ino)
            
            item = self.byfileid.get(fileid,None)
            if item is None:
                item = CasFSItem(p,s)
                
                self.byfileid[item.fileid] = item
                self.bypath[item.path] = item
                newentries += 1
                newbytes += s.st_size
                log.info("New item %s" % (item.path))
            elif item.update(p,s):
                origentries += 1
                origbytes += s.st_size
            
            item.find_time = find_time

        # Clobber all items that have not been touched
        
        lostentries = 0
        lostbytes = 0
        
        for item in [i for i in self.byfileid.itervalues() if i.find_time != find_time]:
            del self.byfileid[item.fileid]
            del self.bypath[item.path]
            del self.byid[item.cid]
            log.info("Vanished item %s" % (item.path))
            lostentries += 1
            lostbytes += item.size
            
            # del item
            
        log.debug("Add    %d %s" % (newentries, sizestr(newbytes)))
        log.debug("Remove %d %s" % (lostentries,sizestr(lostbytes)))
        log.debug("Update %d %s" % (origentries, sizestr(origbytes)))    

        for item in self.byfileid.itervalues():
            oldid = item.cid
            if item.stale:
                log.info("Refresh item %s" % (item.path))
                item.refresh(self.content)
            if oldid != item.cid:
                try:
                    del self.byid[oldid]
                except:
                    pass
                self.byid[item.cid] = item
            
    def _fetch(self,item):
        """ Fetch content of an item and ensure that it
        matches the id we expect.  If not, update for the
        new id, but return nothing from this fetch """
        
        pass

    def __getstate__(self):
        return dict(version=self.version,item=self.byfileid.values())
    
    def __setstate__(self,state):
        assert state.version == self.version

        self.byid = {}
        self.bypath = {}
        
        for i in state.item:
            ci = CasFSItem(saved=i)
            self.byid[ci.cid] = ci
            self.bypath[ci.path] = ci
            self.byfileid[ci.fileid] = ci
