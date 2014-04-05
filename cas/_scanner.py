#!/usr/bin/python

import sys
import os
from optparse import OptionParser
import csv
import stat

from hashlib import sha512
from base64 import b64encode

def getcid(p,bc=0):
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


    data_format = """

path (relative to root of tree),mtime of file, size of file, short md5, full md5

    Path relative to the root of the tree being scanned
    mtime as seconds since epoch
    size in bytes
    short md5 is md5sum of first 64k of file
    long md5 is md5sum of entire file


The data file needs to be updated if any file in the tree is
    - newer than the data file
    - newer than the mtime recorded in the file
    - missing
    - not listed

    
"""

class FileTreeScanner:

    def makesums(self,r):
        for (d,k,fs) in os.walk(r):
            print "dir %s" % (d)

            for f in fs:
                p = os.path.join(d,f)
                if not os.path.isfile(p): continue
                print "  %s" % (f)
                s = os.stat(p)
                fmt = int(s[stat.ST_MTIME])
                size = s[stat.ST_SIZE]

                cid = getcid(p)

                print cid,size,p



if __name__ == "__main__":
    f = FileTreeScanner()

    for r in sys.argv[1:]:
        f.makesums(r)


