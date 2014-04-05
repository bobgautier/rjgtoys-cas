"""
Work out the break even point for using literal
data instead of an SHA512 sum
"""

from base64 import b64encode

from hashlib import sha512

h = sha512()

h.update("This could be anything, it doesn't matter")

d = b64encode(h.digest(),'._')

print "digest length is",len(d)

dlen = len(d)*3/4

print "data length is",dlen

junk = "x"*dlen

d = b64encode(junk,'._')

print "encoded data length",len(d)

junk += 'x'

d = b64encode(junk,'._')

print "one more byte gives me",len(d)

