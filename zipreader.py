#!/usr/bin/python

import sys
import os

import gzip

import time

# write lines to a zip file, every ten seconds

def reader(path):
    
    with gzip.GzipFile(path,'rb') as m:
        data = m.read()
        print "Got %d bytes of data" % (len(data))
        
if __name__ == "__main__":
    reader(sys.argv[1])

