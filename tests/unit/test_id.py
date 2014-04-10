#
# Tests for the id generators
#

from cas._base import cas_string_to_id, CasItemBuilder, CasId, LITERALSIZE
from cas._files import CasFSItem, OTYPE_FILE, OTYPE_LINK, OTYPE_DIR

import base64

import pytest

# Test simple literal ids

def literal_id(s):
    return 'L'+base64.b64encode(s,'._')

def cas_string_to_id_slow(s):
    b = CasItemBuilder()
    for c in s:
        b.add(c)
    assert b.size == len(s)
    # The builder should never hang onto more
    # than the first few bytes of content
    assert len(b.content) <= LITERALSIZE
    return b.cid

def test_simple_literals():
    
    for s in ('one','two','three','four'):
        expected = literal_id(s)
        assert CasId(expected) == expected
        
        assert cas_string_to_id(s) == expected
        assert cas_string_to_id_slow(s) == expected
        
        s = s*(4096/len(s)) # make a larger target
        
        assert len(s) > LITERALSIZE

        cid = cas_string_to_id(s)
        assert CasId(cid) == cid
        assert cid.startswith('I')
        assert cas_string_to_id_slow(s) == cid

def test_bad_coercion():
    
    for v in (0,'Not Valid',{'a':23}):
        with pytest.raises(TypeError):
            x = CasId(v)

#
# Now test files that contain the above simple content
#

import os
import subprocess
from contextlib import contextmanager

@contextmanager
def tempdir():
    n = os.tmpnam()
    assert not os.path.exists(n)
    os.makedirs(n)
    assert os.path.isdir(n)
    print "created temp dir %s" % (n)
    yield n
    s = subprocess.call(('/bin/rm','-rf', n))
    print "removed temp dir %s" % (n)
    assert s == 0
    assert not os.path.exists(n)

def create_file(d,s):
    p = os.path.join(d,s)
    
    f = open(p,'w')
    f.write(s)
    f.close()
    return p

def create_link(d,s):
    p = os.path.join(d,'link'+s)
    
    os.symlink(s,p)
    
    return p
    
def test_file_item():
    
    with tempdir() as d:
        print d
        for c in ('one','two','three','four'):
            p = create_file(d,c)
            
            cid = literal_id(c)
            
            ps = os.lstat(p)
            s = CasFSItem(p,ps).refresh()
            
            assert s.cid == cid
            assert s.size == len(c)
            assert s.path == p
            assert s.otype == OTYPE_FILE
    
def test_link_item():
    
    with tempdir() as d:
        print d
        for c in ('one','two','three','four'):
            p = create_link(d,c)
            
            cid = literal_id(c)
            
            ps = os.lstat(p)
            s = CasFSItem(p,ps).refresh()
            
            assert s.cid == cid
            assert s.size == len(c)
            assert s.path == p
            assert s.otype == OTYPE_LINK
            
def test_dir_item():
    with tempdir() as d:
        print d
        for c in ('a','b','c'):
            p = os.path.join(d,c)
            os.makedirs(p)
            ps = os.lstat(p)
            s = CasFSItem(p,ps).refresh()
            
            assert s.path == p
            assert s.otype == OTYPE_DIR
