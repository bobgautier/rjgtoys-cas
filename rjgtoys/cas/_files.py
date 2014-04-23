#
# file tree cas
#

"""

This is the docstring for _files.py

"""

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

from rjgtoys import logs

log = logs.getLogger(__name__)

# Default relative path to metadata file

DEFAULT_METADATA='.cas'

# Filesystem object types

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
    d = os.path.normpath(unicode(d))
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
            if isinstance(f,str):
                f = unicode(f,errors='replace')
                log.warning("In %s, fudging non-ascii filename '%s'" % (d,f))

            try:
                p = os.path.join(d,f)
            except UnicodeDecodeError,e:
#                f = unicode.decode(f,strict='replace')
                print type(f)
                f = unicode(f,errors='replace')
                log.error("In directory %s:" % (d))
                log.error("Bad filename %s" % (f))
                log.error("Can I join them up?  %s / %s"  % (d,f))
                raise
            except Exception,e:
                print type(e)
                log.error("Can't handle name %s / %s: %s" % (d,f,e))
                continue

            assert isinstance(p,unicode)

            try:
                s = os.lstat(p)
            except Exception,e:
                log.error("Failed to stat %s: %s" % (p,e))
                continue

            yield (p[suffix:],s)
            
            if stat.S_ISDIR(s.st_mode):
                q.append(p)


kiB=1024
MiB=kiB*1024
GiB=MiB*1024
TiB=GiB*1024
PiB=TiB*1024

def sizestr(s,unit='B'):
    """ Convert a number (usually a size in bytes) to a more
    human-readable string.   Note I'm using power of 2 based
    multipliers just to be clear.
    """
    
    f = float(s)
    for (threshold,suffix) in ((PiB,'Pi'),(TiB,'Ti'),(GiB,'Gi'),(MiB,'Mi'),(kiB,'ki')):
        if f >= threshold:
            return ("%6.1f%s%s" % (f/threshold,suffix,unit)).strip()
    return "%d%s" % (s,unit)

def timestr(t):
    t = time.localtime(t)
    
    return time.strftime("%Y-%m-%d %H:%M:%S",t)

def gzipread(path):
    log.debug("gzipread %s" % (path))
        
    with GzipFile(path,'rb') as f:
        return f.read()

def gzipwrite(path,data):

    pathbak = path+'.bak'
    pathtmp = path+'.tmp'
    
    log.debug("gzipwrite %s" % (path)) 
    try:
        os.unlink(pathbak)
        log.debug("gzipwrite removed old backup")
    except:
        pass
    
    try:
        os.unlink(pathtmp)
        log.debug("gzipwrite removed old temp file")
    except:
        pass

    with GzipFile(pathtmp,'wb') as f:
        f.write(data)
        f.flush()

    try:
        os.rename(path,pathbak)
        log.debug("gzipwrite renamed previous to backup")
    except Exception,e:
        if os.path.exists(path):
            log.error("Failed to rename %s to %s" % (path,pathbak))

    try:
        os.rename(pathtmp,path)
        log.debug("gzipwrite renamed temp to %s" % (path))
    except Exception,e:
        log.error("Failed to rename %s to %s" % (pathtmp,path))

class CasFSItem(object):
    """
    A filesystem item: the object contains all you need to know
    to be able to recreate the object, except the (file or link)
    content.
    """
    
    version="1"
    
    def __init__(self,path=None,stat=None,expiry=None,saved=None):

        if saved is not None:
            return self.__setstate__(saved)

        self.__dict__['version'] = self.version
        
        self.expiry = expiry
        self.path = path
        self.clear()
        if path is not None and stat is not None:
            self.update(path,stat)

    def update(self,path,s,force_stale=False):
        """
        Update the info held here if necessary and
        return True if the content id is likely to have changed
        """

        self.path = path
        
        self.stale = force_stale
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
        """
        Update the content id
        """

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

    
    # One day I'll need to do a more general 'print an item'
    # mechanism that will deal with items that know less (or more)
    # about items than this one but for now I'll do something simple...
    
    def printable(self):

        p = unicode.encode(self.path,errors='replace')
        return "%s %s:%s %s %s %s" % (self.otype,self.uname,self.gname,sizestr(self.size),timestr(self.mtime),p)

    @property
    def expired(self):
        return expired(self.expiry)

    def __getstate__(self):
        return self.__dict__
        
    def __setstate__(self,state):
        assert state.version == self.version
        self.__dict__.update(state)
        self.fileid = tuple(self.fileid) # JSON will represent this as a list

        
class CasFileTreeStore(CasStoreBase):

    version="1"
    
    def __init__(self,content=None,metadata=None,refresh=None):
        if content is not None:
            content = os.path.normpath(content)
        self.content = content
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
            data = gzipread(path)
            self.__setstate__(cas_from_json(data))
            return True
        except Exception,e:
            if isinstance(e,IOError) and e.errno == 2:  # Not found
                log.debug("(No metadata found at %s)" % (path))
                return False
            log.error("Failed to load metadata %s:%s" % (path,e))

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
            m = cas_to_json(self)
            log.verbose("Metadata size %d bytes" % (len(m)))

            gzipwrite(path,m)
            
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

    def refresh(self,force=False,checkpoint=0):
        """
        Refresh metadata for this store.
        
        Needs to be split up more to enable:
        
        1) Checkpointing
        2) Progress reporting
        """

        newentries = 0
        newbytes = 0
        
        origentries = 0
        origbytes = 0

        find_time = time.time()
        
        log_time = find_time    # crude progress reporting

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
                log.debug("New item %s" % (item.path))
            elif item.update(p,s,force):
                # If the item needs a reread...
                origentries += 1
                origbytes += s.st_size
                log.debug("Updated item %s" % (item.path))
            
            item.find_time = find_time
            t = time.time()
            if (t-log_time) > 1:
                log.verbose("Scanning: found %d/%s new %d/%s changed" % (newentries,sizestr(newbytes),origentries,sizestr(origbytes)))
                log_time = t

        # Clobber all items that have not been touched
        
        lostentries = 0
        lostbytes = 0
        
        for item in [i for i in self.byfileid.itervalues() if i.find_time != find_time]:
            del self.byfileid[item.fileid]
            del self.bypath[item.path]
            del self.byid[item.cid]
            log.debug("Vanished item %s" % (item.path))
            lostentries += 1
            lostbytes += item.size
            
            t = time.time()
            if (t-log_time) > 1:
                log.verbose("Scanning: found %d/%s deleted" % (lostentries,sizestr(lostbytes)))
                log_time = t
                
            # del item
        
        log.verbose("Scan found %d/%s new %d/%s changed %d/%s deleted" % (
                newentries, sizestr(newbytes),
                origentries, sizestr(origbytes),
                lostentries,sizestr(lostbytes)))

        # refresh phase
        
        refentries = 0
        refbytes = 0
        staleentries = origentries + newentries
        stalebytes = origbytes + newbytes
        
        refstart = time.time()

        if checkpoint:
            log.info("Doing first checkpoint save")
            if not self.save():
                log.error("Cannot save metadata - giving up")
                return
            cp_time = refstart

        for item in self.byfileid.itervalues():
            if not item.stale:
                continue
                
            log.info("Refresh item %s" % (item.path))
            
            oldid = item.cid
            item.refresh(self.content)
            refentries += 1
            refbytes += item.size

            if oldid != item.cid:
                try:
                    del self.byid[oldid]
                except:
                    pass
                self.byid[item.cid] = item
            # FIXME: track path changes too?

            t = time.time()
            if (t-log_time) > 1:
                countpc = int(refentries*100./staleentries)    # percent done by count
                bytespc = int(refbytes*100./stalebytes)        # percent done by bytes
        
                reftogo = ((t-refstart)*(stalebytes-refbytes))/refbytes  #
                eta = t+reftogo
                
                eta = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(eta))
                
                log.verbose("Refreshing: done %d/%d=%d%% %s/%s=%d%% in %ds, %ds to go ETA %s" % (
                            refentries, staleentries, countpc,
                                sizestr(refbytes),sizestr(stalebytes),bytespc,
                                t-refstart,reftogo,eta))
                if (checkpoint > 0) and ((t-cp_time) > checkpoint):
                    log.info("Doing checkpoint save")
                    if not self.save():
                        log.error("Cannot save metadata - giving up")
                        return
                    cp_time = t
                else:
                    log.verbose("No checkpoint this time %d %d" % (checkpoint,t-cp_time))
                    
                log_time = t

        log.info("Refresh completed.")
            
    def _fetch(self,item):
        """ Fetch content of an item and ensure that it
        matches the id we expect.  If not, update for the
        new id, but return nothing from this fetch """
        
        pass

    def __getstate__(self):
        
        items = self.byfileid.values()
        
        log.info("__getstate__ saving %d items" % (len(items)))
        
        return dict(version=self.version,item=items)
    
    def __setstate__(self,state):
        assert state.version == self.version

        self.byid = {}
        self.bypath = {}
        
        log.info("__setstate__ loading %d items" % (len(state.item)))
        
        for i in state.item:
#            print "Load %s" % (i)
            ci = CasFSItem(saved=i)
            self.byid[ci.cid] = ci
            self.bypath[ci.path] = ci
            self.byfileid[ci.fileid] = ci
        
        log.info("loaded %d ids, %d paths, %d fileids" % (len(self.byid),len(self.bypath),len(self.byfileid)))
        
