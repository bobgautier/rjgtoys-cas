#
# Tests for the file tree store
#


import os
import subprocess
from contextlib import contextmanager

from cas._base import cas_to_json
from cas._files import CasFileTreeStore, OTYPE_FILE, OTYPE_LINK, OTYPE_DIR

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

def create_file(d,p,s):
    path = os.path.join(d,p)
    
    f = open(path,'w')
    f.write(s)
    f.close()
    return p

def create_link(d,p,s):
    p = os.path.join(d,p)
    
    os.symlink(s,p)
    
    return p

def item_by_path(s,p):
    for i in s:
        if i.path == p:
            return i
    return None
    
def assert_item_by_path(s,p,otype):
    i = item_by_path(s,p)
    assert i.otype == otype

def test_cas_filetree():
    with tempdir() as d:
        
        create_file(d,'one','content for one')
        create_file(d,'two','content for two')
        ds = os.path.join(d,'sub')
        os.makedirs(ds)
        create_file(ds,'three','content for file three')
        create_link(ds,'link','destination')
        
        s = CasFileTreeStore(content=d)
        
        paths = [i.path for i in s]
        
        assert_item_by_path(s,'sub',OTYPE_DIR)
        assert_item_by_path(s,'one',OTYPE_FILE)
        assert_item_by_path(s,'two',OTYPE_FILE)
        assert_item_by_path(s,'sub/three',OTYPE_FILE)
        assert_item_by_path(s,'sub/link',OTYPE_LINK)

        js = cas_to_json(s)
        print js
        assert False
