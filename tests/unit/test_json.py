#
# test the json mechanics
#

from rjgtoys.cas._base import CasJson

def test_jsonobj():

    d = dict(a=1,b='b',c=(1,2),d=dict(e=1,f=3))
    
    j1 = CasJson(d)
    
    assert 'a' in j1
    assert j1['a'] == 1
    assert j1.a == 1
    
    assert 'b' in j1
    
    assert j1['b'] == 'b'
    assert j1.b == 'b'
    
    
