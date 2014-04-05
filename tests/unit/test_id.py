#
# Tests for the id generators
#

from cas._base import cas_string_to_id, CasItemBuilder, CasId
import base64

import pytest

# Test simple literal ids

def literal_id(s):
    return 'L'+base64.b64encode(s,'._')


# This is the point at which we expect ids to change format    
LITERALSIZE=66

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
