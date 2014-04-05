#
# base classes for cas
#

import hashlib

class CasItemBuilder(object):
    
    def __init__(self,content=None):
        self.reset()
        if content is not None:
            self.add(content)
            
    def reset(self):
        self.h = sha512()
        self.bc = 0
        
    def add(self,content):
        self.h.update(content)
        self.bc += len(content)
        
    @property
    def size(self):
        return self.bc
        
    @property
    def cid(self):
        return b64encode(h.digest(),'._')


def cas_string_to_id(s):

    return CasItemBuilder(s).cid
    

def cas_path_to_id(p):

    bsize = 1024*1024*128

    assert(bsize > bc)

    if bc: bsize = bc

    h = sha512()

    try:
        f = os.open(p,os.O_RDONLY)
    except Exception,e:
        return None

    while True:
        try:
            buffer = os.read(f,bsize)
        except Exception,e:
            try:
                os.close(f)
            except:
                pass
            return None

        if not buffer:
            break
        h.update(buffer)

        if bc:
            break

    os.close(f)

    return b64encode(h.digest(),'._')


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
    if isinstance(ci,basestring):
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

def CasStoreVolatile(CasStoreBase):
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
            
        if size > len(content):
            raise ItemCorruptError()
            
        trueid = cas_string_to_id(content[:size])
        
        if cid is not None and cid != trueid:
            raise ItemCorruptError()
            
        self.items[trueid] = (expiry,size,content[:size])

    def fetch(self,ci):
        
        ci = cas_cid(ci)
        (exp,size,content) = self.items[ci]
        
        if exp < time.time():
            del self.items[ci]
            raise ItemNotFoundError()
            
        return content

    def get_item(self,ci):
        """
        Returns the full content item without the content.
        Could be a no-op in some cases.
        """
        
        ci = cas_cid(ci)
        
        
    def get_expiry(self,ci):
        
        ci = cas_cid(ci)
        
        (exp,size,content) = self.items[ci]
        
        return exp
        
    def get_size(self,ci):
        
        

def CasStore(x):
    print "CasStore",x

    return ['%s%d' % (x,n) for n in range(0,10)]
