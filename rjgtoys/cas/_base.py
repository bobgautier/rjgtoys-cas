#
# base classes for cas
#

"""

This is the documentation for rjgtoys.cas._base

.. autoclass:: CasItemBuilder

"""

from _xc import CasErrorXC, ItemNotFoundError
from _expiry import expired

import hashlib
import base64
import os
import time
import mmap
import json

# Size of block we'll read from a file

BLOCKSIZE=1024*1024*128

__doc__ +="""

.. :py:data:: LITERALSIZE

For very short pieces of data, the 'usual' way of generating
a content id, by taking the SHA512 hash and ``base64`` encoding it,
would produce a content id that is longer than the data itself.

`LITERALSIZE` is the break-even length.

Data items shorter than this length will be encoded into content
ids by using the data directly.

This is admittedly a security/privacy risk since unlike other kinds
of content id, these 'literal' content ids can easily be converted
back into the original data.

The reason the literal content ids are still ``base64`` encoded is to ensure
that they don't contain awkward characters.

"""

LITERALSIZE=66

# Id types

__doc__+="""

Each content id starts with a character that identifies the kind
of content id.

There are currently three kinds defined:

+------------------+-------------+------------------------------------------------------------------+
| Name             | Starts with | Description                                                      |
+==================+=============+==================================================================+
| `CAS_ID_LITERAL` | `L`         | This is a literal id, constructed directly from the (short) data |
+------------------+-------------+------------------------------------------------------------------+
| `CAS_ID_SHA512`  | `I`         | This id is a base64-encoded SHA512 hash of the data              |
+------------------+-------------+------------------------------------------------------------------+
| `CAS_ID_EMPTY`   | `Z`         | The data was zero length; the id for that is simply `Z`          |
+------------------+-------------+------------------------------------------------------------------+

"""

CAS_ID_LITERAL='L'  # Prefix for literal ids
CAS_ID_SHA512='I'   # Prefix for sha512 ids
CAS_ID_EMPTY='Z'    # (Prefix for) the id for theempty string

class CasItemBuilder(object):
    
    """
    Constructs the content id of a string.
    
    The content may be passed to the constructor or fed in incrementally
    using :meth:`add`, or some combination of the two.

    A :class:`CasItemBuilder` may be reused by calling its :meth:`reset`
    before starting each new item.

    .. automethod:: reset
    .. automethod:: add
    .. autoattribute:: size
    .. autoattribute:: cid
    
    """

    def __init__(self,content=None):
        
        self.reset()
        if content is not None:
            self.add(content)
            
    def reset(self):
        """Resets the state of the :class:`CasItemBuilder` so that it
        can be used to generate the cid and size of another data string.
        """
        
        self.h = hashlib.sha512()
        self.bc = 0
        self.content = ''
        
    def add(self,content):
        """Adds more content to the item being examined; changes the
        :attr:`size` and :attr:`cid` properties.
        """

        self.h.update(content)
        self.bc += len(content)
        if self.bc < LITERALSIZE:
            self.content += str(content[:LITERALSIZE])
            
    @property
    def size(self):
        """The number of bytes scanned so far (since the last :meth:`reset`) (Readonly)
        """

        return self.bc
        
    @property
    def cid(self):
        """The content id of the data examined so far (since
        the last :meth:`reset`) (Readonly)
        """

        if self.bc == 0:
            return CAS_ID_EMPTY
        if self.bc < LITERALSIZE:
            return CAS_ID_LITERAL+base64.b64encode(self.content,'._')

        return CAS_ID_SHA512+base64.b64encode(self.h.digest(),'._')


def cas_string_to_id(s):

    return CasItemBuilder(s).cid

def cas_link_to_id(p,bc=None):
    
    if bc == 0:
        return CAS_ID_EMPTY
        
    d = os.readlink(p)
    if bc is not None and len(d) != bc:
        return None
    
    return cas_string_to_id(d)
    
def cas_file_to_id(p,bc=None):

    if bc == 0:
        return CAS_ID_EMPTY
        
    try:
        f = os.open(p,os.O_RDONLY)
    except:
        return None
    
    try:
        return cas_fileno_to_id(f,bc)
    finally:
        os.close(f)

def cas_fileno_to_id(f,bc=None):

    if bc == 0:
        return CAS_ID_EMPTY
        
    try:
        d = mmap.mmap(f,0,mmap.MAP_SHARED,mmap.PROT_READ)
    except Exception,e:
        print "Failed to map: %s" % (e)
        return None
    
    try:
        return cas_bytes_to_id(d,bc=None)
    finally:
        d.close()

def cas_bytes_to_id(b,bc=None):

    if bc is not None and bc != len(b):
        return None

    return CasItemBuilder(b).cid

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
    """
    This is the base class of CAS implementations.   It defines
    the most basic interface to a CAS.
    """
    
    def items(self):
        """
        Generate the sequence of objects in this store
        """
        
        pass
        
    def get(self,ci):
        """
        Get the data associated with this ci
        
        Can raise :exception:`ItemNotFoundError` or :exception:`ItemCorruptedError`
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
        """Implements the *in* operator"""

        return False


class CasStoreVolatile(CasStoreBase):
    """
    A very trivial implementation, mostly for testing,
    that stores content in-memory (just a dict).
    """
    
    def __init__(self):
        self.item = {}
        
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
            
        self.item[trueid] = (expiry,size,content[:size])
        return trueid

    def __contains__(self,ci):
        ci = CasId(ci)
        
        return ci in self.item
        
    def fetch(self,ci):
        
        ci = CasId(ci)
        (exp,size,content) = self.item[ci]
        
        if expired(exp):
            del self.item[ci]
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
        
        (exp,size,content) = self.item[ci]
        
        return exp
        
    def get_size(self,ci):
        
        ci = CasId(ci)
        
        (exp,size,content) = self.item[ci]
        
        return size


def CasStore(x,**kwargs):
    """Factor functions that produces a :class:`CasStoreBase` implementation
    based on the parameters it is passed.
    
    Currently it will only produce :class:`CasFileTreeStore` instances.
    """
    
    print "CasStore",x

    if os.path.isdir(x):
        from _files import CasFileTreeStore
        return CasFileTreeStore(content=x,**kwargs)
    
    raise TypeError("Can't identify a store called '%s'" % (x))

class CasJSONEncoder(json.JSONEncoder):
    
    def default(self,c):
        if hasattr(c,'__getstate__'):
            return c.__getstate__()

        return json.JSONEncoder.default(self,c)

        
def cas_to_json(c):
    return CasJSONEncoder().encode(c)


class CasJson(dict):
    """ A simple class that provides for JS-style
    attribute access: d.x and d['x'] work for any x
    """
    def __getattr__(self, attr):
        return self.get(attr, None)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

def cas_from_json(j):
    return json.loads(j,object_hook=CasJson)
