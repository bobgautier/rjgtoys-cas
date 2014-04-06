#
# base classes for cas
#

from _xc import CasErrorXC, ItemNotFoundError
from _expiry import expired

import hashlib
import base64
import pwd
import grp
import stat
import os
import time

# Size of block we'll read from a file

BLOCKSIZE=1024*1024*128

#
# The following constant is the minimu length of data
# at which it is worth using the SHA512 hash instead of
# the data itself.
#
# When we use the data itself, we base64 encode it,
# which will expand it by a third, so the break even
# point is when the expanded data will be as long
# as a base64 encoded SHA512 checksum
#

LITERALSIZE=66

class CasItemBuilder(object):
    
    def __init__(self,content=None):
        self.reset()
        if content is not None:
            self.add(content)
            
    def reset(self):
        self.h = hashlib.sha512()
        self.bc = 0
        self.content = ''
        
    def add(self,content):
        self.h.update(content)
        self.bc += len(content)
        if self.bc < LITERALSIZE:
            self.content += content
            
    @property
    def size(self):
        return self.bc
        
    @property
    def cid(self):
        if self.bc < LITERALSIZE:
            return 'L'+base64.b64encode(self.content,'._')

        return 'I'+base64.b64encode(self.h.digest(),'._')


def cas_string_to_id(s):

    return CasItemBuilder(s).cid
    

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



class CasStat(object):
    """
    Similar to the os.stat call, except it returns
    the content id too.
    """
    
    def __init__(self,path=None):
        
        if path is not None:
            self.stat(path)
        
    def stat(self,path):
        self.path = path
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
        
        s = os.lstat(path)
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

def cas_link_to_id(p,bc=None):
    
    d = os.readlink(p)
    if bc is not None and len(d) != bc:
        return None
    
    return cas_string_to_id(d)
    
def cas_file_to_id(p,bc=None):

    bsize = BLOCKSIZE

    h = CasItemBuilder()

    try:
        f = os.open(p,os.O_RDONLY)
    except Exception,e:
        return None

    while True:
        try:
            buff = os.read(f,bsize)
        except Exception,e:
            try:
                os.close(f)
            except:
                pass
            return None

        if not buff:
            break
        h.add(buff)

    os.close(f)

    if bc is not None and bc != h.size:
        return None

    return h.cid


class CasItemId(object):
    """
    A CasItemId contains the tiny bit of metadata that
    the store holds about an item.  But it can't find
    the item itself.
    
    Arguably the expiry time is excess: it might vary
    from one store to another.
    """
    
    def __init__(self,cid=None,size=None,expires=None):
        self._cid = cid
        self._size = size
        self._expires = expires

    @property
    def cid(self):
        return self._cid
        
    @property
    def size(self):
        return self._size
        
    @property
    def expires(self):
        return self._expires

def CasId(ci):
    """ This function is used to coerce parameters
    to be content ids, making methods capable of
    accepting ids in various forms
    """
    
    if isinstance(ci,basestring):
        if ci.startswith('I') or ci.startswith('L'):
            return ci
    try:
        return ci.cid
    except:
        pass
        
    raise TypeError("%s is not a caS Id" % (ci))

class CasStoreBase(object):
    
    def items(self):
        """
        Generate sequence of objects in this store
        """
        
        pass
        
    def get(self,ci):
        """
        Get the data associated with this ci
        
        Can raise ItemNotFoundError or ItemCorruptedError
        """
        
        return None

    def put_stream(self,s,expiry=None,size=None,ci=None):
        """
        Store the stream s with expiry specified
        
        Return the contentitem
        
        Limit the size if size is not None
        
        If the cid is given, check that the stream content
        matches, and if not fail with ItemCorruptError
        """
        
        return self.put(s.read(),expiry,size,cid)
                
    def __contains__(self,cid):
        return False


class CasStoreVolatile(CasStoreBase):
    """
    A very trivial implementation, mostly for testing,
    that stores content in-memory (just a dict).
    """
    
    def __init__(self):
        self.items = {}
        
    def store(self,content,expiry=None,size=None,ci=None):
        """
        Store the content with specified expiry
        
        Limit the size if not None
        
        Check the cid if given
        """
        
        if size is None:
            size = len(content)
            
        if size != len(content):
            raise ItemCorruptError()
            
        trueid = cas_string_to_id(content)
        
        if ci is not None and CasId(ci) != trueid:
            raise ItemCorruptError()
            
        self.items[trueid] = (expiry,size,content[:size])
        return trueid

    def __contains__(self,ci):
        ci = CasId(ci)
        
        return ci in self.items
        
    def fetch(self,ci):
        
        ci = CasId(ci)
        (exp,size,content) = self.items[ci]
        
        if expired(exp):
            del self.items[ci]
            raise ItemNotFoundError()
            
        return content

    def get_item(self,ci):
        """
        Returns the full content item without the content.
        Could be a no-op in some cases.
        """
        
        ci = CasId(ci)
        return ci

    def get_expiry(self,ci):
        
        ci = CasId(ci)
        
        (exp,size,content) = self.items[ci]
        
        return exp
        
    def get_size(self,ci):
        
        ci = CasId(ci)
        
        (exp,size,content) = self.items[ci]
        
        return size


def CasStore(x):
    print "CasStore",x

    return ['%s%d' % (x,n) for n in range(0,10)]

if __name__ == "__main__":
    import sys
    
    for x in sys.argv[1:]:
        print x,cas_string_to_id(x)
        
        
