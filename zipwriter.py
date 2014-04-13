#!/usr/bin/python

import sys
import os

import gzip

import time

# write lines to a zip file, every ten seconds

def writer(path):
    
    n = 0
    while True:
        fillfile(path,n)
        time.sleep(10)
        n += 1

def fillfile(path,n):
    
    with gzip.GzipFile(path,'wb') as m:
        data = "\n".join("Line %d" % (i) for i in range(1,n))
        print "Writing %d bytes" % (len(data))
        m.write(data)
        m.flush()
        
if __name__ == "__main__":
    writer(sys.argv[1])

